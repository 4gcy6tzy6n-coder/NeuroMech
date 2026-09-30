#!/usr/bin/env python3
"""Paired objective-transfer dose-curve analysis."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; SEEDS=np.arange(74000,74030);SIZES=(64,256,1024);KAPPAS=np.round(np.arange(-.5,.5001,.1),2);ARMS=("MODE_GAIN_FILTER","CONSTANT_GAIN_FILTER","LINEAR_BILINEAR_RNN","BAYES_ORACLE")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ci_cross(a,seed):
    rng=np.random.default_rng(seed);boot=np.empty(10000)
    for start in range(0,len(boot),128):
        n=min(128,len(boot)-start);si=rng.integers(0,a.shape[0],(n,a.shape[0]));ei=rng.integers(0,a.shape[1],(n,a.shape[1]));boot[start:start+n]=a[si[:,:,None],ei[:,None,:]].mean((1,2))
    return np.quantile(boot,[.025,.975]).tolist()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_DECISION_CONTEXT_DOSE_V1/canonical');d=ap.parse_args().results_dir.resolve();man=json.loads((d/'run_manifest.json').read_text());assert sha(d/'episode_metrics.csv')==man['files']['episode_metrics.csv']
    shape=(30,3,11,256,4);arr=np.full(shape,np.nan,np.float64);sidx={int(v):i for i,v in enumerate(SEEDS)};zidx={v:i for i,v in enumerate(SIZES)};kidx={f'{v:.2f}':i for i,v in enumerate(KAPPAS)};aidx={v:i for i,v in enumerate(ARMS)}
    with (d/'episode_metrics.csv').open() as f:
        for r in csv.DictReader(f):arr[sidx[int(r['training_seed'])],zidx[int(r['train_size'])],kidx[r['kappa']],int(r['episode_id']),aidx[r['arm']]]=float(r['correct'])
    assert np.isfinite(arr).all();curve=[];per_size=[];primary_cube=np.full((30,256,11),np.nan)
    for ki,k in enumerate(KAPPAS):
        diff=arr[:,:,ki,:,aidx['MODE_GAIN_FILTER']]-arr[:,:,ki,:,aidx['CONSTANT_GAIN_FILTER']]
        pooled=diff.mean(axis=1);primary_cube[:,:,ki]=pooled
        row={'kappa':float(k),'mode_accuracy':float(arr[:,:,ki,:,aidx['MODE_GAIN_FILTER']].mean()),'constant_accuracy':float(arr[:,:,ki,:,aidx['CONSTANT_GAIN_FILTER']].mean()),'mode_minus_constant_accuracy':float(pooled.mean()),'crossed_95ci':[float(x) for x in ci_cross(pooled,20261017+ki)],'positive_seed_count':int((pooled.mean(axis=1)>0).sum())}
        for arm in ('LINEAR_BILINEAR_RNN','BAYES_ORACLE'):
            dcomp=arr[:,:,ki,:,aidx['MODE_GAIN_FILTER']]-arr[:,:,ki,:,aidx[arm]];sm=dcomp.mean(axis=(1,2));rng=np.random.default_rng(20262000+ki+aidx[arm]);boot=sm[rng.integers(0,len(sm),(10000,len(sm)))].mean(axis=1)
            row[f'mode_minus_{arm.lower()}_accuracy']=float(dcomp.mean());row[f'mode_minus_{arm.lower()}_seed_ci95']=[float(x) for x in np.quantile(boot,[.025,.975])]
        curve.append(row)
        for zi,ntrain in enumerate(SIZES):
            dsize=diff[:,zi,:];per_size.append({'kappa':float(k),'train_size':ntrain,'mode_minus_constant_accuracy':float(dsize.mean()),'crossed_95ci':[float(x) for x in ci_cross(dsize,20263000+ki*10+zi)],'positive_seed_count':int((dsize.mean(axis=1)>0).sum())})
    point_crossings=[]
    for left,right in zip(curve,curve[1:]):
        ya,yb=left['mode_minus_constant_accuracy'],right['mode_minus_constant_accuracy']
        if ya<=0<yb:point_crossings.append(float(left['kappa']-ya*(right['kappa']-left['kappa'])/(yb-ya)))
    rng=np.random.default_rng(20264001);cross_boot=[]
    for start in range(0,10000,32):
        b=min(32,10000-start);si=rng.integers(0,30,(b,30));ei=rng.integers(0,256,(b,256));curves=primary_cube[si[:,:,None],ei[:,None,:],:].mean((1,2))
        for vals in curves:
            for j in range(10):
                if vals[j]<=0<vals[j+1]:cross_boot.append(float(KAPPAS[j]-vals[j]*(KAPPAS[j+1]-KAPPAS[j])/(vals[j+1]-vals[j])));break
    summary={'experiment_id':'M2_DECISION_CONTEXT_DOSE_V1','classification':'exploratory artificial objective-transfer study','primary':'terminal accuracy(mode gain)-accuracy(constant gain), equally averaged across training sizes','bootstrap':'crossed resampling over training seeds and paired trial IDs','bootstrap_replicates':10000,'rows':int(arr.size),'dose_curve':curve,'per_size':per_size,'zero_crossings_linear_interpolation':point_crossings,'zero_crossing_crossed_bootstrap_95ci':np.quantile(cross_boot,[.025,.975]).tolist() if cross_boot else None,'zero_crossing_bootstrap_fraction':len(cross_boot)/10000}
    (d/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');
    with (d/'per_seed_contrasts.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['training_seed','train_size','kappa','mode_minus_constant_accuracy'])
        for si,seed in enumerate(SEEDS):
            for zi,ntrain in enumerate(SIZES):
                for ki,k in enumerate(KAPPAS):w.writerow([int(seed),ntrain,f'{k:.2f}',float((arr[si,zi,ki,:,aidx['MODE_GAIN_FILTER']]-arr[si,zi,ki,:,aidx['CONSTANT_GAIN_FILTER']]).mean())])
    man['files']['summary.json']=sha(d/'summary.json');man['files']['per_seed_contrasts.csv']=sha(d/'per_seed_contrasts.csv');man['analysis_sources']={'analyzer':sha(Path(__file__)),'runner':sha(Path(__file__).with_name('run_experiment.py')),'contract':sha(ROOT/'summery/M2_DECISION_CONTEXT_DOSE_V1/CONTRACT.md'),'verifier':sha(Path(__file__).with_name('verify_results.py'))};(d/'run_manifest.json').write_text(json.dumps(man,indent=2)+'\n')
    print(json.dumps({'rows':man['rows'],'dose_curve':curve},indent=2))
if __name__=='__main__':main()

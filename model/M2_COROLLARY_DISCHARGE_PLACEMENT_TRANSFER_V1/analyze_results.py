#!/usr/bin/env python3
"""Analyze paired outcomes from the feedback-placement experiment."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];EXP='M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1'
SEEDS=np.arange(88000,88030);HAZARDS=(.01,.05,.20);ARMS=('SENSORY_SITE_CD','OUTPUT_SITE_PERSISTENCE','NO_FEEDBACK','GENERIC_RNN_2H','BAYES_FILTER')
METRICS=('accuracy','false_action_switch_rate','switch_recovery_lag')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ci(x,seed):
    rng=np.random.default_rng(seed);b=np.empty(10000)
    for start in range(0,10000,128):
        n=min(128,10000-start);s=rng.integers(0,30,(n,30));e=rng.integers(0,512,(n,512));b[start:start+n]=x[s[:,:,None],e[:,None,:]].mean((1,2))
    return np.quantile(b,[.025,.975]).tolist()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results'/EXP/'canonical');d=ap.parse_args().results_dir.resolve();man=json.loads((d/'run_manifest.json').read_text());assert man['experiment_id']==EXP and sha(d/'episode_metrics.csv')==man['files']['episode_metrics.csv']
    si={int(v):i for i,v in enumerate(SEEDS)};hi={v:i for i,v in enumerate(HAZARDS)};ai={v:i for i,v in enumerate(ARMS)};mi={v:i for i,v in enumerate(METRICS)}
    arr=np.full((30,3,512,5,3),np.nan,np.float64);keys=set()
    with (d/'episode_metrics.csv').open() as f:
        for r in csv.DictReader(f):
            k=(int(r['training_seed']),float(r['hazard']),int(r['episode_id']),r['arm']);assert k not in keys;keys.add(k)
            for m in METRICS:arr[si[k[0]],hi[k[1]],k[2],ai[k[3]],mi[m]]=float(r[m]) if r[m] else np.nan
    assert len(keys)==30*3*512*5 and np.isfinite(arr[:,:,:,:,:2]).all()
    summary={'experiment_id':EXP,'classification':man['classification'],'primary':'accuracy(SENSORY_SITE_CD)-accuracy(OUTPUT_SITE_PERSISTENCE) at hazard 0.05','bootstrap':'paired crossed resampling of training seeds and shared test episode IDs','bootstrap_replicates':10000,'rows':len(keys),'means':{},'primary_contrast':{},'secondary_accuracy_contrasts':{}}
    for h,hazard in enumerate(HAZARDS):
        summary['means'][str(hazard)]={}
        for a,arm in enumerate(ARMS):
            summary['means'][str(hazard)][arm]={'accuracy':float(arr[:,h,:,a,mi['accuracy']].mean()),'false_action_switch_rate':float(arr[:,h,:,a,mi['false_action_switch_rate']].mean()),'switch_recovery_lag_mean_over_switches':float(np.nanmean(arr[:,h,:,a,mi['switch_recovery_lag']])) if np.isfinite(arr[:,h,:,a,mi['switch_recovery_lag']]).any() else None}
        summary['secondary_accuracy_contrasts'][str(hazard)]={}
        for j,arm in enumerate(ARMS[1:]):
            delta=arr[:,h,:,ai['SENSORY_SITE_CD'],mi['accuracy']]-arr[:,h,:,ai[arm],mi['accuracy']]
            summary['secondary_accuracy_contrasts'][str(hazard)][f'SENSORY_SITE_CD_minus_{arm}']={'mean':float(delta.mean()),'crossed_95ci_descriptive':[float(v) for v in ci(delta,20261023+h*20+j)]}
    h=hi[.05];delta=arr[:,h,:,ai['SENSORY_SITE_CD'],mi['accuracy']]-arr[:,h,:,ai['OUTPUT_SITE_PERSISTENCE'],mi['accuracy']]
    summary['primary_contrast']={'mean_sensory_minus_output_accuracy':float(delta.mean()),'crossed_95ci':[float(v) for v in ci(delta,20261022)],'positive_training_seed_count':int((delta.mean(axis=1)>0).sum())}
    (d/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    man['files']['summary.json']=sha(d/'summary.json');man['analysis_sources']={'runner':sha(ROOT/'model'/EXP/'run_experiment.py'),'analyzer':sha(Path(__file__)),'verifier':sha(ROOT/'model'/EXP/'verify_results.py'),'contract':sha(ROOT/'summery'/EXP/'CONTRACT.md')};(d/'run_manifest.json').write_text(json.dumps(man,indent=2)+'\n')
    print(json.dumps({'primary_contrast':summary['primary_contrast'],'means':summary['means']},indent=2))
if __name__=='__main__':main()

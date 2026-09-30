#!/usr/bin/env python3
"""Analyze paired closed-loop target pursuit results."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];SEEDS=np.arange(75000,75030);CONDS=('ALIGNED','REVERSED');ARMS=('MODE_GAIN','NO_CONTEXT','ADDITIVE_RNN_MATCHED','BILINEAR_RNN_MATCHED','KALMAN_ORACLE');METRICS=('final_distance','success','mean_distance','steps_to_success')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def crossed_ci(x,seed):
    rng=np.random.default_rng(seed);boot=np.empty(10000)
    for start in range(0,10000,128):
        n=min(128,10000-start);si=rng.integers(0,30,(n,30));ei=rng.integers(0,256,(n,256));boot[start:start+n]=x[si[:,:,None],ei[:,None,:]].mean((1,2))
    return np.quantile(boot,[.025,.975]).tolist()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_2D_CLOSED_LOOP_PURSUIT_V1/canonical');d=ap.parse_args().results_dir.resolve();man=json.loads((d/'run_manifest.json').read_text());assert sha(d/'episode_metrics.csv')==man['files']['episode_metrics.csv']
    arr=np.full((30,2,256,5,4),np.nan,np.float64);sidx={int(v):i for i,v in enumerate(SEEDS)};cidx={v:i for i,v in enumerate(CONDS)};aidx={v:i for i,v in enumerate(ARMS)};midx={v:i for i,v in enumerate(METRICS)}
    with (d/'episode_metrics.csv').open() as f:
        for r in csv.DictReader(f):
            for m in METRICS:arr[sidx[int(r['training_seed'])],cidx[r['condition']],int(r['episode_id']),aidx[r['arm']],midx[m]]=float(r[m])
    assert np.isfinite(arr).all();summary={'experiment_id':'M2_2D_CLOSED_LOOP_PURSUIT_V1','classification':'exploratory artificial sensorimotor study','primary':'ALIGNED final_distance(BILINEAR_RNN_MATCHED)-final_distance(MODE_GAIN); positive favors mode gain','bootstrap':'crossed resampling over training seeds and paired target episodes','bootstrap_replicates':10000,'rows':int(arr.shape[0]*arr.shape[1]*arr.shape[2]*arr.shape[3]),'mean_metrics':{},'contrasts':{}}
    seed_contrasts=[]
    pairs=(('bilinear_minus_mode','BILINEAR_RNN_MATCHED','MODE_GAIN'),('additive_minus_mode','ADDITIVE_RNN_MATCHED','MODE_GAIN'),('no_context_minus_mode','NO_CONTEXT','MODE_GAIN'),('oracle_minus_mode','KALMAN_ORACLE','MODE_GAIN'))
    for ci,condition in enumerate(CONDS):
        summary['mean_metrics'][condition]={}
        for arm,ai in aidx.items():summary['mean_metrics'][condition][arm]={m:float(arr[:,ci,:,ai,midx[m]].mean()) for m in METRICS}
        summary['contrasts'][condition]={}
        for pair_i,(pair,left,right) in enumerate(pairs):
            for metric in ('final_distance','success'):
                diff=arr[:,ci,:,aidx[left],midx[metric]]-arr[:,ci,:,aidx[right],midx[metric]];seed=20261020+ci*100+pair_i*10+midx[metric]
                summary['contrasts'][condition].setdefault(pair,{})[metric]={'mean_left_minus_right':float(diff.mean()),'crossed_95ci':[float(x) for x in crossed_ci(diff,seed)],'positive_seed_count':int((diff.mean(axis=1)>0).sum())}
                if metric=='final_distance':
                    for si,s in enumerate(SEEDS):seed_contrasts.append({'training_seed':int(s),'condition':condition,'contrast':pair,'mean_left_minus_right_final_distance':float(diff[si].mean())})
    (d/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (d/'seed_contrasts.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(seed_contrasts[0]),lineterminator='\n');w.writeheader();w.writerows(seed_contrasts)
    man['files']['summary.json']=sha(d/'summary.json');man['files']['seed_contrasts.csv']=sha(d/'seed_contrasts.csv');man['analysis_sources']={'runner':sha(Path(__file__).with_name('run_experiment.py')),'analyzer':sha(Path(__file__)),'verifier':sha(Path(__file__).with_name('verify_results.py')),'contract':sha(ROOT/'summery/M2_2D_CLOSED_LOOP_PURSUIT_V1/CONTRACT.md')};(d/'run_manifest.json').write_text(json.dumps(man,indent=2)+'\n')
    print(json.dumps({'aligned_mean_metrics':summary['mean_metrics']['ALIGNED'],'aligned_contrasts':summary['contrasts']['ALIGNED']},indent=2))
if __name__=='__main__':main()

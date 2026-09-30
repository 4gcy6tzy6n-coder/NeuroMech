#!/usr/bin/env python3
"""Independent completeness, hash, and bootstrap verification for the 2D pursuit run."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];SEEDS=np.arange(75000,75030);CONDS=('ALIGNED','REVERSED');ARMS=('MODE_GAIN','NO_CONTEXT','ADDITIVE_RNN_MATCHED','BILINEAR_RNN_MATCHED','KALMAN_ORACLE');METRICS=('final_distance','success','mean_distance','steps_to_success')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ci(x,seed):
    rng=np.random.default_rng(seed);boot=np.empty(10000)
    for start in range(0,10000,128):
        n=min(128,10000-start);si=rng.integers(0,30,(n,30));ei=rng.integers(0,256,(n,256));boot[start:start+n]=x[si[:,:,None],ei[:,None,:]].mean((1,2))
    return np.quantile(boot,[.025,.975])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_2D_CLOSED_LOOP_PURSUIT_V1/canonical');d=ap.parse_args().results_dir.resolve();man=json.loads((d/'run_manifest.json').read_text());assert man['experiment_id']=='M2_2D_CLOSED_LOOP_PURSUIT_V1'
    for name,digest in man['files'].items():assert sha(d/name)==digest,(name,'hash')
    src=man['analysis_sources'];
    for key,file in [('runner','run_experiment.py'),('analyzer','analyze_results.py'),('verifier','verify_results.py')]:assert sha(ROOT/'model/M2_2D_CLOSED_LOOP_PURSUIT_V1'/file)==src[key]
    assert sha(ROOT/'summery/M2_2D_CLOSED_LOOP_PURSUIT_V1/CONTRACT.md')==src['contract']
    sidx={int(v):i for i,v in enumerate(SEEDS)};cidx={v:i for i,v in enumerate(CONDS)};aidx={v:i for i,v in enumerate(ARMS)};midx={v:i for i,v in enumerate(METRICS)};arr=np.full((30,2,256,5,4),np.nan,np.float64);keys=set();n=0
    with (d/'episode_metrics.csv').open() as f:
      for r in csv.DictReader(f):
        k=(int(r['training_seed']),r['condition'],int(r['episode_id']),r['arm']);assert k not in keys;keys.add(k)
        for m in METRICS:arr[sidx[k[0]],cidx[k[1]],k[2],aidx[k[3]],midx[m]]=float(r[m])
        n+=1
    assert n==30*2*256*5 and np.isfinite(arr).all();assert (arr[:,:,:,:,midx['final_distance']]>=0).all();assert set(np.unique(arr[:,:,:,:,midx['success']])).issubset({0.,1.})
    summ=json.loads((d/'summary.json').read_text());assert summ['rows']==n;pairs=(('bilinear_minus_mode','BILINEAR_RNN_MATCHED','MODE_GAIN'),('additive_minus_mode','ADDITIVE_RNN_MATCHED','MODE_GAIN'),('no_context_minus_mode','NO_CONTEXT','MODE_GAIN'),('oracle_minus_mode','KALMAN_ORACLE','MODE_GAIN'));checks=0
    for ci0,condition in enumerate(CONDS):
        for pair_i,(pair,left,right) in enumerate(pairs):
            for metric in ('final_distance','success'):
                diff=arr[:,ci0,:,aidx[left],midx[metric]]-arr[:,ci0,:,aidx[right],midx[metric]];stored=summ['contrasts'][condition][pair][metric];assert abs(diff.mean()-stored['mean_left_minus_right'])<1e-12
                seed=20261020+ci0*100+pair_i*10+midx[metric];assert np.allclose(ci(diff,seed),stored['crossed_95ci'],atol=1e-12);checks+=1
    print(json.dumps({'status':'PASS','rows':n,'unique_keys':len(keys),'crossed_intervals_recomputed':checks,'source_and_output_hashes':'PASS'},indent=2))
if __name__=='__main__':main()

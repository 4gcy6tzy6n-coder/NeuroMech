#!/usr/bin/env python3
"""Check output completeness, provenance, and primary decision-task dose contrasts."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];SEEDS=np.arange(74000,74030);SIZES=(64,256,1024);KAPPAS=np.round(np.arange(-.5,.5001,.1),2);ARMS=("MODE_GAIN_FILTER","CONSTANT_GAIN_FILTER","LINEAR_BILINEAR_RNN","BAYES_ORACLE")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_DECISION_CONTEXT_DOSE_V1/canonical');d=ap.parse_args().results_dir.resolve();man=json.loads((d/'run_manifest.json').read_text());assert man['experiment_id']=='M2_DECISION_CONTEXT_DOSE_V1'
    for name,digest in man['files'].items():assert sha(d/name)==digest,(name,'sha256')
    src=man['analysis_sources'];assert sha(ROOT/'model/M2_DECISION_CONTEXT_DOSE_V1/run_experiment.py')==src['runner'];assert sha(ROOT/'model/M2_DECISION_CONTEXT_DOSE_V1/analyze_results.py')==src['analyzer'];assert sha(ROOT/'model/M2_DECISION_CONTEXT_DOSE_V1/verify_results.py')==src['verifier'];assert sha(ROOT/'summery/M2_DECISION_CONTEXT_DOSE_V1/CONTRACT.md')==src['contract']
    sidx={int(v):i for i,v in enumerate(SEEDS)};zidx={v:i for i,v in enumerate(SIZES)};kidx={f'{v:.2f}':i for i,v in enumerate(KAPPAS)};aidx={v:i for i,v in enumerate(ARMS)};arr=np.full((30,3,11,256,4),np.nan,np.float64);keys=set();n=0
    with (d/'episode_metrics.csv').open() as f:
      for r in csv.DictReader(f):
        key=(int(r['training_seed']),int(r['train_size']),r['kappa'],int(r['episode_id']),r['arm']);assert key not in keys;keys.add(key);v=float(r['correct']);assert v in (0.,1.);arr[sidx[key[0]],zidx[key[1]],kidx[key[2]],key[3],aidx[key[4]]]=v;n+=1
    assert n==30*3*11*256*4 and np.isfinite(arr).all()
    summary=json.loads((d/'summary.json').read_text());assert summary['rows']==n;checks=0
    for ki,k in enumerate(KAPPAS):
        diff=arr[:,:,ki,:,aidx['MODE_GAIN_FILTER']]-arr[:,:,ki,:,aidx['CONSTANT_GAIN_FILTER']];pooled=diff.mean(axis=1);stored=summary['dose_curve'][ki];assert abs(pooled.mean()-stored['mode_minus_constant_accuracy'])<1e-12
        rng=np.random.default_rng(20261017+ki);boot=np.empty(10000)
        for start in range(0,10000,128):
            b=min(128,10000-start);si=rng.integers(0,30,(b,30));ei=rng.integers(0,256,(b,256));boot[start:start+b]=pooled[si[:,:,None],ei[:,None,:]].mean((1,2))
        assert np.allclose(np.quantile(boot,[.025,.975]),stored['crossed_95ci'],atol=1e-12);checks+=1
    print(json.dumps({'status':'PASS','rows':n,'unique_keys':len(keys),'dose_points_recomputed':checks,'primary_bootstrap_intervals_recomputed':checks,'provenance_hashes':'PASS'},indent=2))
if __name__=='__main__':main()

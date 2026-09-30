#!/usr/bin/env python3
"""Independent integrity and estimand check for M2 context-information dose response."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SEEDS=np.arange(43000,43030); KAPPAS=np.round(np.arange(-.5,.5001,.1),2)
POLICIES=("MODE_GAIN_FILTER","CONSTANT_GAIN_FILTER","GENERIC_RNN_1D","BILINEAR_RNN_1D","KALMAN_ORACLE")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_CONTEXT_INFORMATION_DOSE_V1/canonical');d=ap.parse_args().results_dir.resolve()
    man=json.loads((d/'run_manifest.json').read_text()); assert man['experiment_id']=='M2_CONTEXT_INFORMATION_DOSE_V1'
    assert man['rows']==len(SEEDS)*len(KAPPAS)*256*len(POLICIES)
    for name,digest in man['files'].items(): assert sha(d/name)==digest,(name,'hash')
    src=man['analysis_source_sha256']; assert sha(ROOT/'model/M2_CONTEXT_INFORMATION_DOSE_V1/run_experiment.py')==src['runner']
    assert sha(ROOT/'model/M2_CONTEXT_INFORMATION_DOSE_V1/analyze_results.py')==src['analyzer']
    assert sha(ROOT/'model/M2_CONTEXT_INFORMATION_DOSE_V1/verify_results.py')==src['verifier']
    assert sha(ROOT/'summery/M2_CONTEXT_INFORMATION_DOSE_V1/CONTRACT.md')==src['contract']
    pidx={p:i for i,p in enumerate(POLICIES)};kidx={f'{k:.2f}':i for i,k in enumerate(KAPPAS)};sidx={int(s):i for i,s in enumerate(SEEDS)}
    cube=np.full((30,11,256,5),np.nan,np.float64); keys=set(); row_count=0
    with (d/'episode_metrics.csv').open() as f:
      for r in csv.DictReader(f):
        key=(int(r['train_seed']),r['kappa'],int(r['episode_id']),r['policy']); assert key not in keys;keys.add(key)
        value=float(r['episode_mse']); assert np.isfinite(value) and value>=0
        cube[sidx[key[0]],kidx[key[1]],key[2],pidx[key[3]]]=value;row_count+=1
    assert row_count==man['rows'] and np.isfinite(cube).all()
    summary=json.loads((d/'summary.json').read_text()); assert summary['rows']==row_count
    checks=0
    for ki,k in enumerate(KAPPAS):
      r=summary['dose_curve'][ki]; assert abs(r['kappa']-k)<1e-10
      con=cube[:,ki,:,pidx['CONSTANT_GAIN_FILTER']]; mode=cube[:,ki,:,pidx['MODE_GAIN_FILTER']]; diff=con-mode
      assert abs(float(diff.mean())-r['constant_minus_mode'])<1e-11
      assert abs(float(mode.mean())-r['mode_gain_mse'])<1e-11
      assert abs(float(con.mean())-r['constant_gain_mse'])<1e-11
      rng=np.random.default_rng(72061+ki);boot=np.empty(10000)
      for start in range(0,10000,128):
        n=min(128,10000-start); si=rng.integers(0,30,(n,30));ei=rng.integers(0,256,(n,256))
        boot[start:start+n]=diff[si[:,:,None],ei[:,None,:]].mean(axis=(1,2))
      assert np.allclose(np.quantile(boot,[.025,.975]),r['crossed_95ci'],atol=1e-12)
      checks+=1
    print(json.dumps({'status':'PASS','rows':row_count,'unique_keys':len(keys),'dose_points_recomputed':checks,'primary_crossed_bootstraps_recomputed':checks,'source_and_output_hashes':'PASS'},indent=2))
if __name__=='__main__':main()

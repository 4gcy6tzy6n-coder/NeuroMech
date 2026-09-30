#!/usr/bin/env python3
"""Independent integrity and estimand check for archived M2 gate results."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_FORWARD_STATE_SENSORY_GATE_V2'); d=ap.parse_args().results_dir
 man=json.loads((d/'manifest.json').read_text()); assert man['experiment_id']=='M2_FORWARD_STATE_SENSORY_GATE_V2'
 for name,digest in man['sha256'].items(): assert sha(d/name)==digest,(name,'checksum mismatch')
 rows=list(csv.DictReader((d/'episode_metrics.csv').open())); assert len(rows)==20*3*512*5, len(rows)
 assert len({(r['train_seed'],r['condition'],r['episode_id'],r['policy']) for r in rows})==len(rows)
 s=json.loads((d/'summary.json').read_text())['summary']; observed={}
 for ci,c in enumerate(('ALIGNED','INDEPENDENT','REVERSED')):
  values={}
  for r in rows:
   if r['condition']==c and r['policy'] in ('MODE_GAIN_FILTER','GENERIC_RNN_1D','CONSTANT_GAIN_FILTER'):
    values.setdefault((int(r['train_seed']),int(r['episode_id'])),{})[r['policy']]=float(r['episode_mse'])
  assert len(values)==20*512
  g=np.array([[values[(seed,ep)]['GENERIC_RNN_1D']-values[(seed,ep)]['MODE_GAIN_FILTER'] for ep in range(512)] for seed in range(42000,42020)])
  a=np.array([[values[(seed,ep)]['CONSTANT_GAIN_FILTER']-values[(seed,ep)]['MODE_GAIN_FILTER'] for ep in range(512)] for seed in range(42000,42020)])
  assert abs(g.mean()-s[c]['primary_contrast']['generic_minus_mode_mse'])<1e-10
  assert abs(a.mean()-s[c]['mechanism_ablation_contrast']['constant_minus_mode_mse'])<1e-10
  rng=np.random.default_rng(20261006+ci+1); boot=np.empty(20000)
  for start in range(0,len(boot),128):
   n=min(128,len(boot)-start); si=rng.integers(0,20,(n,20)); ei=rng.integers(0,512,(n,512)); boot[start:start+n]=a[si[:,:,None],ei[:,None,:]].mean(axis=(1,2))
  ci_re=np.quantile(boot,[.025,.975]); ci_rec=s[c]['mechanism_ablation_contrast']['crossed_95_percent_bootstrap_interval']
  assert np.allclose(ci_re,ci_rec,atol=1e-10), (c,ci_re,ci_rec)
  observed[c]={'generic_minus_mode':float(g.mean()),'constant_minus_mode':float(a.mean()),'ablation_ci':ci_re.tolist()}
 aligned={}
 for r in rows:
  if r['condition']=='ALIGNED' and r['policy'] in ('MODE_GAIN_FILTER','GENERIC_RNN_1D'):
   aligned.setdefault((int(r['train_seed']),int(r['episode_id'])),{})[r['policy']]=float(r['episode_mse'])
 rng=np.random.default_rng(20261005); g=np.array([[aligned[(seed,ep)]['GENERIC_RNN_1D']-aligned[(seed,ep)]['MODE_GAIN_FILTER'] for ep in range(512)] for seed in range(42000,42020)])
 boot=np.empty(20000)
 for start in range(0,len(boot),128):
  n=min(128,len(boot)-start); si=rng.integers(0,20,(n,20)); ei=rng.integers(0,512,(n,512)); boot[start:start+n]=g[si[:,:,None],ei[:,None,:]].mean(axis=(1,2))
 assert np.allclose(np.quantile(boot,[.025,.975]),s['ALIGNED']['primary_contrast']['crossed_95_percent_bootstrap_interval'],atol=1e-10)
 print(json.dumps({'status':'PASS','metric_rows':len(rows),'contrasts_recomputed':observed,'checksums':'PASS'},indent=2))
if __name__=='__main__':main()

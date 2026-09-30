#!/usr/bin/env python3
"""Independent integrity, row-count, and primary estimand verification for V3."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_FORWARD_STATE_SENSORY_GATE_V3');d=ap.parse_args().results_dir;man=json.loads((d/'manifest.json').read_text());assert man['experiment_id']=='M2_FORWARD_STATE_SENSORY_GATE_V3'
 for n,h in man['sha256'].items():assert sha(d/n)==h,(n,'checksum mismatch')
 rows=list(csv.DictReader((d/'episode_metrics.csv').open()));assert len(rows)==20*3*3*512*6,len(rows);unique={(r['train_seed'],r['environment'],r['condition'],r['episode_id'],r['policy']) for r in rows};assert len(unique)==len(rows)
 report=json.loads((d/'summary.json').read_text())['summary'];envs=('IN_RANGE','HIGH_PERSISTENCE','LOW_PERSISTENCE');conds=('ALIGNED','INDEPENDENT','REVERSED');policies=('MODE_GAIN_FILTER','CONSTANT_GAIN_FILTER','GENERIC_RNN_1D','BILINEAR_RNN_1D','GRU_1D','KALMAN_ORACLE');comp={'constant_minus_mode':('CONSTANT_GAIN_FILTER','MODE_GAIN_FILTER'),'generic_minus_mode':('GENERIC_RNN_1D','MODE_GAIN_FILTER'),'bilinear_minus_mode':('BILINEAR_RNN_1D','MODE_GAIN_FILTER'),'gru_minus_mode':('GRU_1D','MODE_GAIN_FILTER')};verify_count=0;primary=None
 for env_i,env in enumerate(envs):
  for cond_i,cond in enumerate(conds):
   mats={p:np.empty((20,512)) for p in policies}
   for r in rows:
    if r['environment']==env and r['condition']==cond:mats[r['policy']][int(r['train_seed'])-42000,int(r['episode_id'])]=float(r['episode_mse'])
   for j,(name,(lhs,rhs)) in enumerate(comp.items()):
    diff=mats[lhs]-mats[rhs];stored=report[env][cond]['contrasts'][name];assert abs(float(diff.mean())-stored['mean_difference'])<1e-10,(env,cond,name,'mean')
    rng=np.random.default_rng(20261005+env_i*100+cond_i*10+j);boot=np.empty(20000)
    for start in range(0,len(boot),128):
     n=min(128,len(boot)-start);si=rng.integers(0,20,(n,20));ei=rng.integers(0,512,(n,512));boot[start:start+n]=diff[si[:,:,None],ei[:,None,:]].mean((1,2))
    assert np.allclose(np.quantile(boot,[.025,.975]),stored['crossed_95_percent_bootstrap_interval'],atol=1e-10),(env,cond,name,'CI');verify_count+=1
    if env=='IN_RANGE' and cond=='ALIGNED' and name=='constant_minus_mode':primary={'difference':float(diff.mean()),'ci':stored['crossed_95_percent_bootstrap_interval']}
 print(json.dumps({'status':'PASS','metric_rows':len(rows),'unique_rows':len(unique),'recomputed_contrasts_and_intervals':verify_count,'primary':primary,'checksums':'PASS'},indent=2))
if __name__=='__main__':main()

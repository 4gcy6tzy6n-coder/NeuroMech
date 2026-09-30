#!/usr/bin/env python3
"""Build summaries, crossed intervals, and hashes from the archived V3 episode table."""
import csv,hashlib,json,platform
from pathlib import Path
import numpy as np,torch
ROOT=Path(__file__).resolve().parents[2];ID='M2_FORWARD_STATE_SENSORY_GATE_V3'
ENVS=('IN_RANGE','HIGH_PERSISTENCE','LOW_PERSISTENCE');CONDS=('ALIGNED','INDEPENDENT','REVERSED')
POLICIES=('MODE_GAIN_FILTER','CONSTANT_GAIN_FILTER','GENERIC_RNN_1D','BILINEAR_RNN_1D','GRU_1D','KALMAN_ORACLE')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def ci(m,seed):
 rng=np.random.default_rng(seed);bs=np.empty(20000)
 for start in range(0,len(bs),128):
  n=min(128,len(bs)-start);si=rng.integers(0,20,(n,20));ei=rng.integers(0,512,(n,512));bs[start:start+n]=m[si[:,:,None],ei[:,None,:]].mean((1,2))
 return [float(x) for x in np.quantile(bs,[.025,.975])]
def main():
 out=ROOT/'data/results'/ID;rows=list(csv.DictReader((out/'episode_metrics.csv').open())); matrices={};summary={}
 for env_i,env in enumerate(ENVS):
  summary[env]={}
  for cond_i,cond in enumerate(CONDS):
   grouped={p:np.empty((20,512),dtype=float) for p in POLICIES}
   sums={p:{'mse':[],'mae':[]} for p in POLICIES}
   for r in rows:
    if r['environment']==env and r['condition']==cond:
     p=r['policy'];s=int(r['train_seed'])-42000;e=int(r['episode_id']);grouped[p][s,e]=float(r['episode_mse']);sums[p]['mse'].append(float(r['episode_mse']));sums[p]['mae'].append(float(r['episode_mae']))
   summary[env][cond]={'policies':{p:{'mean_mse':float(np.mean(sums[p]['mse'])),'mean_mae':float(np.mean(sums[p]['mae']))} for p in POLICIES}}
   summary[env][cond]['contrasts']={}
   comparisons={'constant_minus_mode':('CONSTANT_GAIN_FILTER','MODE_GAIN_FILTER'),'generic_minus_mode':('GENERIC_RNN_1D','MODE_GAIN_FILTER'),'bilinear_minus_mode':('BILINEAR_RNN_1D','MODE_GAIN_FILTER'),'gru_minus_mode':('GRU_1D','MODE_GAIN_FILTER')}
   for j,(name,(a,b)) in enumerate(comparisons.items()):
    m=grouped[a]-grouped[b];summary[env][cond]['contrasts'][name]={'mean_difference':float(m.mean()),'positive_seed_means':int((m.mean(1)>0).sum()),'crossed_95_percent_bootstrap_interval':ci(m,20261005+env_i*100+cond_i*10+j),'n_seeds':20,'n_episodes':512}
   matrices[(env,cond)]=grouped
 primary=summary['IN_RANGE']['ALIGNED']['contrasts']['constant_minus_mode'];primary['primary_estimand']=True
 (out/'summary.json').write_text(json.dumps({'experiment_id':ID,'summary':summary},indent=2)+'\n')
 files=[out/n for n in ('episode_metrics.csv','learned_parameters.csv','training_curves.csv','summary.json')]
 man={'experiment_id':ID,'python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'parameters':{'training_seeds':[42000,42019],'training_episodes_per_seed':512,'test_episodes_per_environment':512,'horizon':160,'updates':300,'primary_bootstrap_replicates':20000,'primary_bootstrap_seed':20261005,'contrast_bootstrap_seed_rule':'20261005 + 100*environment_index + 10*condition_index + comparison_index'},'sha256':{p.name:sha(p) for p in files}}
 (out/'manifest.json').write_text(json.dumps(man,indent=2)+'\n');print(json.dumps({'primary':primary,'conditions':{e:{c:summary[e][c]['contrasts'] for c in CONDS} for e in ENVS}},indent=2))
if __name__=='__main__':main()

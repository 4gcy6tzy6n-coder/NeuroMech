#!/usr/bin/env python3
"""Summarize closed-loop episode outcomes and write immutable hashes."""
import csv,hashlib,json,platform
from pathlib import Path
import numpy as np,torch
ROOT=Path(__file__).resolve().parents[2];ID='M2_CLOSED_LOOP_ACTIVE_SENSING_V1';CONDS=('ALIGNED','INDEPENDENT','REVERSED');POLICIES=('MODE_GAIN_FILTER','CONSTANT_GAIN_FILTER','GENERIC_RNN_1D','BILINEAR_RNN_1D','GRU_1D','BAYESIAN_OBSERVER')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def crossed_ci(m,seed):
 rng=np.random.default_rng(seed);bs=np.empty(20000)
 for start in range(0,len(bs),128):
  n=min(128,len(bs)-start);si=rng.integers(0,20,(n,20));ei=rng.integers(0,512,(n,512));bs[start:start+n]=m[si[:,:,None],ei[:,None,:]].mean((1,2))
 return [float(x) for x in np.quantile(bs,[.025,.975])]
def main():
 out=ROOT/'data/results'/ID;rows=list(csv.DictReader((out/'episode_control.csv').open()));summary={};metrics=('mean_distance','terminal_distance','success');contrasts=('CONSTANT_GAIN_FILTER','GENERIC_RNN_1D','BILINEAR_RNN_1D','GRU_1D','BAYESIAN_OBSERVER')
 for ci,c in enumerate(CONDS):
  group={p:{m:np.empty((20,512),dtype=float) for m in metrics} for p in POLICIES}
  for r in rows:
   if r['condition']==c:
    p=r['policy'];si=int(r['train_seed'])-42000;ei=int(r['episode_id'])
    for m in metrics:group[p][m][si,ei]=float(r[m])
  summary[c]={'policies':{p:{m:float(group[p][m].mean()) for m in metrics} for p in POLICIES},'contrasts':{}}
  for j,p in enumerate(contrasts):
   d=group[p]['mean_distance']-group['MODE_GAIN_FILTER']['mean_distance'];summary[c]['contrasts'][f'{p}_minus_mode_mean_distance']={'mean_difference':float(d.mean()),'positive_seed_means':int((d.mean(1)>0).sum()),'crossed_95_percent_bootstrap_interval':crossed_ci(d,20261008+ci*10+j),'n_seeds':20,'n_episodes':512}
 summary['ALIGNED']['contrasts']['CONSTANT_GAIN_FILTER_minus_mode_mean_distance']['primary']=True
 (out/'summary.json').write_text(json.dumps({'experiment_id':ID,'summary':summary},indent=2)+'\n')
 files=[out/n for n in ('episode_control.csv','learned_parameters.csv','training_curves.csv','summary.json')]
 man={'experiment_id':ID,'python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'parameters':{'train_seeds':[42000,42019],'training_episodes_per_seed':512,'training_steps':250,'test_episodes_per_condition':512,'test_horizon':24,'primary_bootstrap_replicates':20000,'primary_bootstrap_seed':20261008,'contrast_seed_rule':'20261008 + condition_index*10 + comparator_index'},'sha256':{p.name:sha(p) for p in files}}
 (out/'manifest.json').write_text(json.dumps(man,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

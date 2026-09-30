#!/usr/bin/env python3
"""Summarize archived episode rows and write checksummed run metadata."""
import csv,hashlib,json,platform
from pathlib import Path
import numpy as np, torch
ROOT=Path(__file__).resolve().parents[2]; ID='M2_FORWARD_STATE_SENSORY_GATE_V2'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'data/results'/ID; rows=list(csv.DictReader((out/'episode_metrics.csv').open())); seeds=range(42000,42020); conds=('ALIGNED','INDEPENDENT','REVERSED'); policies=('MODE_GAIN_FILTER','GENERIC_RNN_1D','CONSTANT_GAIN_FILTER','CURRENT_OBSERVATION','KALMAN_LINEAR_REFERENCE'); summary={}; matrices={}
 for c in conds:
  summary[c]={}
  for p in policies:
   z=[r for r in rows if r['condition']==c and r['policy']==p]; summary[c][p]={'mean_mse':float(np.mean([float(r['episode_mse']) for r in z])),'mean_mae':float(np.mean([float(r['episode_mae']) for r in z]))}
  values={}
  for r in rows:
   if r['condition']==c and r['policy'] in ('MODE_GAIN_FILTER','GENERIC_RNN_1D','CONSTANT_GAIN_FILTER'):
    values.setdefault((int(r['train_seed']),int(r['episode_id'])),{})[r['policy']]=float(r['episode_mse'])
  a=np.empty((20,512))
  for (seed,ep),v in values.items(): a[seed-42000,ep]=v['GENERIC_RNN_1D']-v['MODE_GAIN_FILTER']
  matrices[c]=a
  summary[c]['primary_contrast']={'generic_minus_mode_mse':float(a.mean()),'positive_seed_means':int((a.mean(1)>0).sum()),'n_seeds':20,'n_episodes':512}
  const_minus_mode=np.array([[values[(s,e)]['CONSTANT_GAIN_FILTER']-values[(s,e)]['MODE_GAIN_FILTER'] for e in range(512)] for s in range(42000,42020)])
  summary[c]['mechanism_ablation_contrast']={'constant_minus_mode_mse':float(const_minus_mode.mean()),'positive_seed_means':int((const_minus_mode.mean(1)>0).sum()),'n_seeds':20,'n_episodes':512}
  rng_ab=np.random.default_rng(20261006+len(summary))
  boot=np.empty(20000)
  for start in range(0,len(boot),128):
   n=min(128,len(boot)-start); si=rng_ab.integers(0,20,(n,20)); ei=rng_ab.integers(0,512,(n,512)); boot[start:start+n]=const_minus_mode[si[:,:,None],ei[:,None,:]].mean(axis=(1,2))
  summary[c]['mechanism_ablation_contrast']['crossed_95_percent_bootstrap_interval']=[float(x) for x in np.quantile(boot,[.025,.975])]
 rng=np.random.default_rng(20261005); a=matrices['ALIGNED']; bs=np.empty(20000)
 for start in range(0,len(bs),128):
  n=min(128,len(bs)-start); si=rng.integers(0,a.shape[0],(n,a.shape[0])); ei=rng.integers(0,a.shape[1],(n,a.shape[1])); bs[start:start+n]=a[si[:,:,None],ei[:,None,:]].mean(axis=(1,2))
 summary['ALIGNED']['primary_contrast']['crossed_95_percent_bootstrap_interval']=[float(x) for x in np.quantile(bs,[.025,.975])]
 (out/'summary.json').write_text(json.dumps({'experiment_id':ID,'summary':summary},indent=2)+'\n')
 files=[out/n for n in ('episode_metrics.csv','learned_parameters.csv','summary.json')]
 manifest={'experiment_id':ID,'python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'parameters':{'train_seeds':[42000,42019],'training_episodes':256,'test_episodes':512,'horizon':160,'updates':250,'bootstrap_replicates':20000,'primary_bootstrap_seed':20261005,'mechanism_ablation_bootstrap_seed_base':20261007},'sha256':{p.name:sha(p) for p in files}}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

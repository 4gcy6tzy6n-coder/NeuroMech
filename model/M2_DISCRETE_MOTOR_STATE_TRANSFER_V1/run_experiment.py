#!/usr/bin/env python3
"""Exploratory transfer test with categorical realized motor-state feedback."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import torch
from torch import nn

ROOT=Path(__file__).resolve().parents[2]
NAME="M2_DISCRETE_MOTOR_STATE_TRANSFER_V1"
ARMS=("SELF_STATE","ZERO_STATE","ACTION_STATE","YOKED_STATE","REACTIVE")
LEARNED=ARMS[:-1]
SEEDS=tuple(910000+i for i in range(32))
T=64; BATCH=32; UPDATES=160; NTEST=128
RHO=.60; GAIN=.40; MOTOR_SD=.025; OBS_SD=.14; BOOT=20_000; BOOT_SEED=8_765_501
PROFILES={
 "TRAIN_LIKE":{"alpha":.91,"missing_fraction":.50,"mean_burst":4.0},
 "LONG_BURST":{"alpha":.91,"missing_fraction":.50,"mean_burst":8.0},
 "LOW_MISSING":{"alpha":.91,"missing_fraction":.25,"mean_burst":4.0},
 "FAST_TARGET":{"alpha":.76,"missing_fraction":.50,"mean_burst":4.0}}

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
 return h.hexdigest()

def write_csv(p:Path,rows:list[dict])->None:
 if not rows: raise ValueError('refusing to write empty csv')
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def make_batch(seed:int,n:int,alpha:float|None,missing_fraction:float,mean_burst:float):
 rng=np.random.default_rng(seed); alphas=rng.uniform(.84,.97,n) if alpha is None else np.full(n,alpha)
 target=np.zeros((n,T),np.float32);target[:,0]=rng.uniform(-1,1,n)
 vel=rng.normal(0,.055,n).astype(np.float32)
 for t in range(1,T):
  vel=alphas*vel+rng.normal(0,.055,n);target[:,t]=target[:,t-1]+vel
 motor_noise=rng.normal(0,MOTOR_SD,(n,T)).astype(np.float32)
 obs_noise=rng.normal(0,OBS_SD,(n,T)).astype(np.float32)
 available=np.ones((n,T),bool)
 if missing_fraction:
  p_leave=min(1,1/mean_burst);p_enter=missing_fraction/(1-missing_fraction)*p_leave
  missing=rng.random(n)<missing_fraction
  for t in range(T):
   if t:
    u=rng.random(n);missing=np.where(missing,u>=p_leave,u<p_enter)
   available[:,t]=~missing
 return target,motor_noise,obs_noise,available

class Controller(nn.Module):
 def __init__(self,seed:int):
  super().__init__();torch.manual_seed(seed);self.cell=nn.GRUCell(3,8);self.readout=nn.Linear(8,1)
 def step(self,x,h):
  h=self.cell(x,h);return torch.tanh(self.readout(h)).squeeze(-1),h

def new_model(seed:int): return Controller(seed)

def derangement(n:int,seed:int)->np.ndarray:
 rng=np.random.default_rng(seed);base=np.arange(n)
 for _ in range(1000):
  ix=rng.permutation(n)
  if np.all(ix!=base):return ix
 raise RuntimeError('failed to construct derangement')

def rollout(model:Controller,arm:str,batch,yoke:np.ndarray|None=None):
 target,mnoise,onoise,available=batch;n=len(target)
 tar=torch.from_numpy(target);mn=torch.from_numpy(mnoise);on=torch.from_numpy(onoise);av=torch.from_numpy(available)
 yoke_t=torch.from_numpy(yoke) if yoke is not None else None
 pos=torch.zeros(n);velocity=torch.zeros(n);previous=torch.zeros(n);h=torch.zeros(n,8)
 err=np.empty((n,T));energy=np.empty((n,T));motor_states=np.empty((n,T),np.int8)
 model.eval()
 with torch.no_grad():
  for t in range(T):
   velocity=RHO*velocity+GAIN*previous+mn[:,t];pos=pos+velocity;relative=tar[:,t]-pos
   obs=torch.where(av[:,t],relative+on[:,t],torch.zeros_like(relative))
   actual_state=torch.where(velocity>=0,1.,-1.)
   if arm=='SELF_STATE':fb=actual_state
   elif arm=='ZERO_STATE':fb=torch.zeros_like(velocity)
   elif arm=='ACTION_STATE':fb=torch.where(previous>=0,1.,-1.)
   elif arm=='YOKED_STATE':
    if yoke_t is None:raise ValueError('yoked arm requires donor trace')
    fb=yoke_t[:,t]
   elif arm=='REACTIVE':
    cmd=torch.where(av[:,t],torch.clamp(.55*obs,-1,1),torch.zeros_like(obs))
    err[:,t]=relative.square().numpy();energy[:,t]=cmd.square().numpy();motor_states[:,t]=actual_state.numpy().astype(np.int8);previous=cmd
    continue
   x=torch.stack((obs,av[:,t].float(),fb),dim=-1);cmd,h=model.step(x,h)
   err[:,t]=relative.square().numpy();energy[:,t]=cmd.square().numpy();motor_states[:,t]=actual_state.numpy().astype(np.int8);previous=cmd
 return {'tracking_mse':err.mean(axis=1),'command_energy':energy.mean(axis=1),'missing_fraction':1-available.mean(axis=1)},motor_states

def train_one(arm:str,seed:int,donor:Controller|None=None):
 model=new_model(seed+1901);opt=torch.optim.Adam(model.parameters(),lr=.003);start=time.perf_counter();last_loss=0.
 for update in range(UPDATES):
  bs=seed+100000+update*7919;data=make_batch(bs,BATCH,None,.50,4.0); donor_drive=None
  if arm=='YOKED_STATE':
   if donor is None:raise ValueError('yoked training requires self-state donor')
   _,donor_states=rollout(donor,'SELF_STATE',data)
   donor_drive=donor_states[derangement(BATCH,bs+33333)].astype(np.float32)
  target,mnoise,onoise,available=data;tar=torch.from_numpy(target);mn=torch.from_numpy(mnoise);on=torch.from_numpy(onoise);av=torch.from_numpy(available)
  pos=torch.zeros(BATCH);velocity=torch.zeros(BATCH);previous=torch.zeros(BATCH);h=torch.zeros(BATCH,8);losses=[]
  yd=torch.from_numpy(donor_drive) if donor_drive is not None else None
  for t in range(T):
   velocity=RHO*velocity+GAIN*previous+mn[:,t];pos=pos+velocity;rel=tar[:,t]-pos
   obs=torch.where(av[:,t],rel+on[:,t],torch.zeros_like(rel));actual_state=torch.where(velocity>=0,1.,-1.)
   if arm=='SELF_STATE':fb=actual_state
   elif arm=='ZERO_STATE':fb=torch.zeros_like(velocity)
   elif arm=='ACTION_STATE':fb=torch.where(previous>=0,1.,-1.)
   elif arm=='YOKED_STATE':fb=yd[:,t]
   x=torch.stack((obs,av[:,t].float(),fb),-1);cmd,h=model.step(x,h)
   losses.append(rel.square()+.002*cmd.square());previous=cmd
  loss=torch.stack(losses,1).mean();opt.zero_grad(set_to_none=True);loss.backward();nn.utils.clip_grad_norm_(model.parameters(),5.);opt.step();last_loss=float(loss.detach())
 flat=[float(x) for p in model.parameters() for x in p.detach().reshape(-1)]
 return model.eval(),{'training_seed':seed,'arm':arm,'parameter_count':sum(p.numel() for p in model.parameters()),'updates':UPDATES,'batch_trajectories':BATCH,'sequence_length':T,'final_training_loss':last_loss,'training_seconds':time.perf_counter()-start,'parameters_json':json.dumps(flat,separators=(',',':'))}

def bootstrap(values):
 x=np.asarray(values,float);rng=np.random.default_rng(BOOT_SEED);draw=x[rng.integers(0,len(x),(BOOT,len(x)))].mean(axis=1)
 return {'mean':float(x.mean()),'ci95_low':float(np.quantile(draw,.025)),'ci95_high':float(np.quantile(draw,.975)),'n_seed_blocks':len(x)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'data/results'/NAME/'canonical');out=ap.parse_args().output_dir.resolve()
 if out.exists() and any(out.iterdir()):raise FileExistsError(f'refusing to overwrite {out}')
 out.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1);fits=[];episodes=[];yoke_checks=[];start=time.time()
 for block,seed in enumerate(SEEDS):
  print(f'training seed block {block+1}/{len(SEEDS)}',flush=True)
  models={}
  for arm in ('SELF_STATE','ZERO_STATE','ACTION_STATE'):
   models[arm],row=train_one(arm,seed);fits.append(row)
  models['YOKED_STATE'],row=train_one('YOKED_STATE',seed,models['SELF_STATE']);fits.append(row)
  for pi,(profile,cfg) in enumerate(PROFILES.items()):
   test_seed=21_000_000+block*100_000+pi*1000;data=make_batch(test_seed,NTEST,cfg['alpha'],cfg['missing_fraction'],cfg['mean_burst'])
   _,self_trace=rollout(models['SELF_STATE'],'SELF_STATE',data);mapping=derangement(NTEST,test_seed+44444);yoke=self_trace[mapping].astype(np.float32)
   exact=bool(np.array_equal(np.sort(self_trace,axis=0),np.sort(yoke,axis=0)))
   yoke_checks.append({'seed_block':block,'profile':profile,'no_fixed_points':bool(np.all(mapping!=np.arange(NTEST))),'exact_per_time_distribution_match':exact})
   all_metrics={}
   for arm in LEARNED:all_metrics[arm]=rollout(models[arm],arm,data,yoke if arm=='YOKED_STATE' else None)[0]
   all_metrics['REACTIVE']=rollout(models['SELF_STATE'],'REACTIVE',data)[0]
   for arm,mets in all_metrics.items():
    for ep in range(NTEST):episodes.append({'seed_block':block,'training_seed':seed,'profile':profile,'evaluation_seed':test_seed,'episode_id':ep,'arm':arm,'tracking_mse':float(mets['tracking_mse'][ep]),'command_energy':float(mets['command_energy'][ep]),'missing_fraction':float(mets['missing_fraction'][ep])})
  print(f'finished seed block {block+1}/{len(SEEDS)}',flush=True)
 write_csv(out/'fit_manifest.csv',fits);write_csv(out/'episode_metrics.csv',episodes);(out/'yoke_checks.json').write_text(json.dumps(yoke_checks,indent=2)+'\n')
 summaries=[]
 for block in range(len(SEEDS)):
  for profile in PROFILES:
   for arm in ARMS:
    rows=[r for r in episodes if r['seed_block']==block and r['profile']==profile and r['arm']==arm]
    summaries.append({'seed_block':block,'profile':profile,'arm':arm,'n_episodes':len(rows),**{m:float(np.mean([r[m] for r in rows])) for m in ('tracking_mse','command_energy','missing_fraction')}})
 write_csv(out/'seed_summary.csv',summaries)
 def mean(block,arm,metric='tracking_mse'):
  return float(next(r for r in summaries if r['seed_block']==block and r['profile']=='LONG_BURST' and r['arm']==arm)[metric])
 contrasts={key:[mean(b,'SELF_STATE')-mean(b,other) for b in range(len(SEEDS))] for key,other in [('self_minus_action','ACTION_STATE'),('self_minus_zero','ZERO_STATE'),('self_minus_yoke','YOKED_STATE'),('self_minus_reactive','REACTIVE')]}
 summary={'experiment':NAME,'classification':'outcome-informed exploratory artificial transfer; discrete movement-state input','training_seed_blocks':len(SEEDS),'fits':len(fits),'episode_rows':len(episodes),'parameter_count_per_learned_arm':sum(p.numel() for p in new_model(0).parameters()),'updates':UPDATES,'primary_profile':'LONG_BURST','primary_contrast':'SELF_STATE minus ACTION_STATE; negative favors realized discrete movement state','contrasts':{k:{'seed_block_values':v,'summary':bootstrap(v)} for k,v in contrasts.items()},'mean_mse_by_profile_arm':{p:{a:float(np.mean([r['tracking_mse'] for r in summaries if r['profile']==p and r['arm']==a])) for a in ARMS} for p in PROFILES},'all_yoke_checks_pass':all(x['no_fixed_points'] and x['exact_per_time_distribution_match'] for x in yoke_checks),'scope':'synthetic 1D target tracking; sign of realized velocity; no biological or general AI claim'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
 files=('fit_manifest.csv','episode_metrics.csv','seed_summary.csv','yoke_checks.json','summary.json')
 manifest={'experiment':NAME,'contract_sha256':sha(ROOT/'summery'/NAME/'CONTRACT.md'),'runner_sha256':sha(Path(__file__)),'verifier_sha256':sha(ROOT/'model'/NAME/'verify_results.py'),'python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'device':'CPU','training_seeds':SEEDS,'arms':ARMS,'profiles':PROFILES,'updates':UPDATES,'duration_seconds':time.time()-start,'outputs':{f:{'bytes':(out/f).stat().st_size,'sha256':sha(out/f)} for f in files}}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'status':'COMPLETE','primary':summary['contrasts']['self_minus_action']['summary'],'contrasts':{k:v['summary'] for k,v in summary['contrasts'].items()},'mse':summary['mean_mse_by_profile_arm']},indent=2))

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Test realized binary motor-state feedback over an actuator-mismatch dose."""
from __future__ import annotations
import argparse,csv,hashlib,json,platform,time
from pathlib import Path
import numpy as np
import torch
from torch import nn

ROOT=Path(__file__).resolve().parents[2];NAME='M2_ACTUATION_UNCERTAINTY_STATE_FEEDBACK_V1'
ARMS=('SELF_STATE','ACTION_STATE','ZERO_STATE','YOKED_STATE','REACTIVE');LEARNED=ARMS[:-1]
SEEDS=tuple(range(940000,940032));TEST_LEVELS=(0.0,0.10,0.25,0.40)
T=64;BATCH=32;UPDATES=160;NTEST=128;RHO=.60;GAIN=.40;MOTOR_SD=.025;OBS_SD=.14
BOOT=20_000;BOOT_SEED=8_765_502;DROP_FRAC=.50;DROP_BURST=8.0;TARGET_SD=.055

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def write_csv(p,rs):
 if not rs:raise ValueError(f'empty table {p}')
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)

def make_batch(seed,n,reverse_prob=None,mean_burst=DROP_BURST):
 r=np.random.default_rng(seed);alpha=r.uniform(.84,.97,n)
 p=r.uniform(0,.40,n) if reverse_prob is None else np.full(n,reverse_prob)
 target=np.zeros((n,T),np.float32);target[:,0]=r.uniform(-1,1,n)
 tv=r.normal(0,TARGET_SD,n).astype(np.float32)
 for t in range(1,T):tv=alpha*tv+r.normal(0,TARGET_SD,n);target[:,t]=target[:,t-1]+tv
 motor_noise=r.normal(0,MOTOR_SD,(n,T)).astype(np.float32)
 obs_noise=r.normal(0,OBS_SD,(n,T)).astype(np.float32)
 reverse=r.random((n,T))<p[:,None]
 available=np.ones((n,T),bool);p_leave=1/mean_burst;p_enter=DROP_FRAC/(1-DROP_FRAC)*p_leave
 missing=r.random(n)<DROP_FRAC
 for t in range(T):
  if t:
   u=r.random(n);missing=np.where(missing,u>=p_leave,u<p_enter)
  available[:,t]=~missing
 return {'target':target,'motor_noise':motor_noise,'obs_noise':obs_noise,'reverse':reverse,'available':available,'reverse_prob':p}

class Controller(nn.Module):
 def __init__(self,seed):
  super().__init__();torch.manual_seed(seed);self.cell=nn.GRUCell(3,8);self.out=nn.Linear(8,1)
 def step(self,x,h):
  h=self.cell(x,h);return torch.tanh(self.out(h)).squeeze(-1),h
def new_model(seed):return Controller(seed)
def derangement(n,seed):
 r=np.random.default_rng(seed);ident=np.arange(n)
 for _ in range(1000):
  x=r.permutation(n)
  if np.all(x!=ident):return x
 raise RuntimeError('derangement failed')
def tensors(d):return {k:torch.from_numpy(v) for k,v in d.items() if isinstance(v,np.ndarray)}

def rollout(model,arm,d,yoke=None):
 n=len(d['target']);dt=tensors(d);tar=dt['target'];mn=dt['motor_noise'];on=dt['obs_noise'];rev=dt['reverse'];av=dt['available'];yt=torch.from_numpy(yoke) if yoke is not None else None
 pos=torch.zeros(n);vel=torch.zeros(n);pc=torch.zeros(n);h=torch.zeros(n,8);err=np.empty((n,T));energy=np.empty((n,T));state=np.empty((n,T),np.int8)
 model.eval() if model is not None else None
 with torch.no_grad():
  for t in range(T):
   vel=RHO*vel+GAIN*pc+mn[:,t];vel=torch.where(rev[:,t],-vel,vel);pos=pos+vel;rel=tar[:,t]-pos
   obs=torch.where(av[:,t],rel+on[:,t],torch.zeros_like(rel));actual=torch.where(vel>=0,1.,-1.)
   if arm=='REACTIVE':cmd=torch.where(av[:,t],torch.clamp(.55*obs,-1,1),torch.zeros_like(obs))
   else:
    if arm=='SELF_STATE':fb=actual
    elif arm=='ACTION_STATE':fb=torch.where(pc>=0,1.,-1.)
    elif arm=='ZERO_STATE':fb=torch.zeros_like(pc)
    elif arm=='YOKED_STATE':
     if yt is None:raise ValueError('yoked evaluation needs donor motor states')
     fb=yt[:,t]
    x=torch.stack((obs,av[:,t].float(),fb),-1);cmd,h=model.step(x,h)
   err[:,t]=rel.square().numpy();energy[:,t]=cmd.square().numpy();state[:,t]=actual.numpy().astype(np.int8);pc=cmd
 return {'tracking_mse':err.mean(1),'command_energy':energy.mean(1),'missing_fraction':1-d['available'].mean(1)},state

def train_one(arm,seed,donor=None):
 model=new_model(seed+5101);opt=torch.optim.Adam(model.parameters(),lr=.003);last=0.;start=time.perf_counter()
 for u in range(UPDATES):
  bs=seed+700000+u*7919;d=make_batch(bs,BATCH);yd=None
  if arm=='YOKED_STATE':
   if donor is None:raise ValueError('yoke fit requires self-state donor')
   _,states=rollout(donor,'SELF_STATE',d);yd=states[derangement(BATCH,bs+33_333)].astype(np.float32)
  dt=tensors(d);tar=dt['target'];mn=dt['motor_noise'];on=dt['obs_noise'];rev=dt['reverse'];av=dt['available'];yyt=torch.from_numpy(yd) if yd is not None else None
  pos=torch.zeros(BATCH);vel=torch.zeros(BATCH);pc=torch.zeros(BATCH);h=torch.zeros(BATCH,8);losses=[]
  for t in range(T):
   vel=RHO*vel+GAIN*pc+mn[:,t];vel=torch.where(rev[:,t],-vel,vel);pos=pos+vel;rel=tar[:,t]-pos
   obs=torch.where(av[:,t],rel+on[:,t],torch.zeros_like(rel));actual=torch.where(vel>=0,1.,-1.)
   if arm=='SELF_STATE':fb=actual
   elif arm=='ACTION_STATE':fb=torch.where(pc>=0,1.,-1.)
   elif arm=='ZERO_STATE':fb=torch.zeros_like(pc)
   elif arm=='YOKED_STATE':fb=yyt[:,t]
   x=torch.stack((obs,av[:,t].float(),fb),-1);cmd,h=model.step(x,h)
   losses.append(rel.square()+.002*cmd.square());pc=cmd
  L=torch.stack(losses,1).mean();opt.zero_grad(set_to_none=True);L.backward();nn.utils.clip_grad_norm_(model.parameters(),5.);opt.step();last=float(L.detach())
 fit={'training_seed':seed,'arm':arm,'parameter_count':sum(p.numel() for p in model.parameters()),'updates':UPDATES,'batch_trajectories':BATCH,'steps':T,'final_training_loss':last,'training_seconds':time.perf_counter()-start,'parameters_json':json.dumps([float(x) for p in model.parameters() for x in p.detach().reshape(-1)],separators=(',',':'))}
 return model.eval(),fit

def boot(x):
 a=np.asarray(x,float);r=np.random.default_rng(BOOT_SEED);draw=a[r.integers(0,len(a),(BOOT,len(a)))].mean(1)
 return {'mean':float(a.mean()),'ci95_low':float(np.quantile(draw,.025)),'ci95_high':float(np.quantile(draw,.975)),'n_seed_blocks':len(a)}

def run(out,seeds=SEEDS,ntest=NTEST,report=True):
 if out.exists() and any(out.iterdir()):raise FileExistsError(f'refusing to overwrite {out}')
 out.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1);fits=[];eps=[];yoke_checks=[];t0=time.time()
 for b,seed in enumerate(seeds):
  print(f'training seed block {b+1}/{len(seeds)}',flush=True);models={}
  for arm in ('SELF_STATE','ACTION_STATE','ZERO_STATE'):
   models[arm],fit=train_one(arm,seed);fits.append(fit)
  models['YOKED_STATE'],fit=train_one('YOKED_STATE',seed,models['SELF_STATE']);fits.append(fit)
  for li,p in enumerate(TEST_LEVELS):
   test_seed=22_000_000+b*10_000+li*1000;d=make_batch(test_seed,ntest,p)
   _,donor=rollout(models['SELF_STATE'],'SELF_STATE',d);ix=derangement(ntest,test_seed+44444);yoke=donor[ix].astype(np.float32)
   exact=bool(np.array_equal(np.sort(donor,axis=0),np.sort(yoke,axis=0)))
   yoke_checks.append({'seed_block':b,'reverse_probability':p,'no_fixed_points':bool(np.all(ix!=np.arange(ntest))),'exact_per_time_distribution_match':exact})
   metrics={}
   for arm in LEARNED:metrics[arm]=rollout(models[arm],arm,d,yoke if arm=='YOKED_STATE' else None)[0]
   metrics['REACTIVE']=rollout(None,'REACTIVE',d)[0]
   for arm,ms in metrics.items():
    for ep in range(ntest):eps.append({'seed_block':b,'training_seed':seed,'reverse_probability':p,'evaluation_seed':test_seed,'episode_id':ep,'arm':arm,'tracking_mse':float(ms['tracking_mse'][ep]),'command_energy':float(ms['command_energy'][ep]),'missing_fraction':float(ms['missing_fraction'][ep])})
  print(f'finished seed block {b+1}/{len(seeds)}',flush=True)
 write_csv(out/'fit_manifest.csv',fits);write_csv(out/'episode_metrics.csv',eps);(out/'yoke_checks.json').write_text(json.dumps(yoke_checks,indent=2)+'\n')
 seedsums=[]
 for b in range(len(seeds)):
  for p in TEST_LEVELS:
   for arm in ARMS:
    rr=[r for r in eps if r['seed_block']==b and r['reverse_probability']==p and r['arm']==arm]
    seedsums.append({'seed_block':b,'reverse_probability':p,'arm':arm,'n_episodes':len(rr),**{m:float(np.mean([r[m] for r in rr])) for m in ('tracking_mse','command_energy','missing_fraction')}})
 write_csv(out/'seed_summary.csv',seedsums)
 def m(b,arm,p):return float(next(r['tracking_mse'] for r in seedsums if r['seed_block']==b and r['arm']==arm and r['reverse_probability']==p))
 adv={str(p):[m(b,'ACTION_STATE',p)-m(b,'SELF_STATE',p) for b in range(len(seeds))] for p in TEST_LEVELS}
 interactions=[adv['0.4'][b]-adv['0.0'][b] for b in range(len(seeds))]
 controls={name:{'seed_block_values':[m(b,'SELF_STATE',p)-m(b,other,p) for b in range(len(seeds))],'summary':boot([m(b,'SELF_STATE',p)-m(b,other,p) for b in range(len(seeds))])} for name,other in [('self_minus_zero','ZERO_STATE'),('self_minus_yoke','YOKED_STATE'),('self_minus_reactive','REACTIVE')] for p in [0.4]}
 summary={'experiment':NAME,'classification':'outcome-informed exploratory; motor-state information dose test','training_seed_blocks':len(seeds),'fit_rows':len(fits),'episode_rows':len(eps),'seed_summary_rows':len(seedsums),'learned_parameters':sum(p.numel() for p in new_model(0).parameters()),'updates':UPDATES,'test_levels':TEST_LEVELS,'primary_estimand':'(ACTION_STATE MSE - SELF_STATE MSE) at p_reverse=.40 minus same contrast at p_reverse=0','advantage_by_reverse_probability':{p:{'seed_block_values':v,'summary':boot(v)} for p,v in adv.items()},'primary_interaction_seed_block_values':interactions,'primary_interaction_summary':boot(interactions),'p_reverse_040_secondary_controls':controls,'mean_mse_by_p_arm':{str(p):{arm:float(np.mean([r['tracking_mse'] for r in seedsums if r['reverse_probability']==p and r['arm']==arm])) for arm in ARMS} for p in TEST_LEVELS},'all_yoke_checks_pass':all(r['no_fixed_points'] and r['exact_per_time_distribution_match'] for r in yoke_checks),'scope':'synthetic 1D target tracking; categorical actual movement feedback; no biological or general AI claim'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
 fs=('fit_manifest.csv','episode_metrics.csv','seed_summary.csv','yoke_checks.json','summary.json')
 man={'experiment':NAME,'contract_sha256':sha(ROOT/'summery'/NAME/'CONTRACT.md'),'runner_sha256':sha(Path(__file__)),'verifier_sha256':sha(ROOT/'model'/NAME/'verify_results.py'),'python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'device':'CPU','training_seeds':list(seeds),'test_levels':TEST_LEVELS,'arms':ARMS,'updates':UPDATES,'duration_seconds':time.time()-t0,'outputs':{f:{'bytes':(out/f).stat().st_size,'sha256':sha(out/f)} for f in fs}}
 (out/'manifest.json').write_text(json.dumps(man,indent=2)+'\n')
 if report:print(json.dumps({'status':'COMPLETE','primary':summary['primary_interaction_summary'],'dose_advantage':{p:v['summary'] for p,v in summary['advantage_by_reverse_probability'].items()}},indent=2))
 return summary
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'data/results'/NAME/'canonical');a=ap.parse_args();run(a.output_dir)
if __name__=='__main__':main()

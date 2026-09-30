#!/usr/bin/env python3
"""Exploratory synthetic transfer test of forward-state sensory gating."""
import argparse, csv, hashlib, json, platform
from pathlib import Path
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2]
ID="M2_FORWARD_STATE_SENSORY_GATE_V1"
SEEDS=range(42000,42020); NTRAIN=256; NTEST=512; T=160; UPDATES=120
PHI=.97; QSW=.05; PROC=np.sqrt(.05); SIGMA=.25; CONDITIONS=("ALIGNED","INDEPENDENT","REVERSED")
POLICIES=("MODE_GAIN_FILTER","GENERIC_RNN_1D","CONSTANT_GAIN_FILTER","CURRENT_OBSERVATION","KALMAN_LINEAR_REFERENCE")

def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def H(q,c):
 if c=="ALIGNED": return (q>0).astype(np.float32)
 if c=="INDEPENDENT": return np.full(q.shape,.5,np.float32)
 if c=="REVERSED": return (q<0).astype(np.float32)
 raise ValueError(c)
def data(seed,n,c):
 r=np.random.default_rng(seed); x=np.zeros(n,np.float32); q=r.choice([-1,1],n).astype(np.int8)
 ys=[]; xs=[]; qs=[]
 for t in range(T):
  if t: x=PHI*x+r.normal(0,PROC,n).astype(np.float32); q=np.where(r.random(n)<QSW,-q,q).astype(np.int8)
  xs.append(x.copy()); qs.append(q.copy()); ys.append(H(q,c)*x+r.normal(0,SIGMA,n).astype(np.float32))
 return np.stack(xs,1),np.stack(qs,1),np.stack(ys,1).astype(np.float32)
def rollout(raw,y,q,f):
 n,t=y.shape; s=torch.zeros(n); out=[]
 if f=="MODE_GAIN_FILTER":
  rho=.999*torch.sigmoid(raw[0]); gp=torch.sigmoid(raw[1]+raw[2]); gm=torch.sigmoid(raw[1]-raw[2]); b=.2*torch.tanh(raw[3])
  for k in range(t):
   p=rho*s; g=torch.where(q[:,k]>0,gp,gm); s=p+g*(y[:,k]-p)+b; out.append(s)
 elif f=="GENERIC_RNN_1D":
  for k in range(t): s=torch.tanh(raw[0]*y[:,k]+raw[1]*q[:,k]+raw[2]*s+raw[3]); out.append(s)
 elif f=="CONSTANT_GAIN_FILTER":
  rho=.999*torch.sigmoid(raw[0]); g=torch.sigmoid(raw[1]); b=.2*torch.tanh(raw[2])
  for k in range(t): p=rho*s; s=p+g*(y[:,k]-p)+b; out.append(s)
 return torch.stack(out,1)
def fit(seed,x,q):
 torch.set_num_threads(1); tx=torch.from_numpy(x); tq=torch.from_numpy(q.astype(np.float32)); starts={"MODE_GAIN_FILTER":[3,0,0,0],"GENERIC_RNN_1D":[.7,0,.6,0],"CONSTANT_GAIN_FILTER":[3,0,0]}; out={}
 for j,(f,init) in enumerate(starts.items()):
  torch.manual_seed(seed+101*(j+1)); p=torch.nn.Parameter(torch.tensor(init,dtype=torch.float32)); opt=torch.optim.Adam([p],lr=.025)
  for _ in range(UPDATES):
   loss=((rollout(p,tx,tq,f)-tx)**2).mean(); opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_([p],5); opt.step()
  out[f]=p.detach().numpy().astype(float).tolist()
 return out
def kalman(y,q,c):
 n,t=y.shape; s=np.zeros(n); v=np.full(n,PROC**2/(1-PHI**2)); out=np.empty_like(y)
 for k in range(t):
  h=H(q[:,k],c); pv=PHI**2*v+PROC**2; gain=pv*h/(h*h*pv+SIGMA**2); p=PHI*s; s=p+gain*(y[:,k]-h*p); v=(1-gain*h)*pv; out[:,k]=s
 return out
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',type=Path,default=ROOT/'data/results'/ID); a=ap.parse_args(); out=a.output_dir.resolve()
 if out.exists() and any(out.iterdir()): raise FileExistsError(out)
 out.mkdir(parents=True,exist_ok=True); evals={c:data(520000+i,NTEST,c) for i,c in enumerate(CONDITIONS)}; rows=[]; params=[]
 for seed in SEEDS:
  x,q,y=data(421000+seed,NTRAIN,'ALIGNED'); fitted=fit(seed,x,q)
  for f,p in fitted.items(): params.append({'train_seed':seed,'policy':f,'n_parameters':len(p),'raw_parameters':json.dumps(p)})
  for c,(tx,tq,ty) in evals.items():
   for f in POLICIES:
    if f in fitted:
     with torch.no_grad(): pred=rollout(torch.tensor(fitted[f],dtype=torch.float32),torch.from_numpy(ty),torch.from_numpy(tq.astype(np.float32)),f).numpy()
    elif f=='CURRENT_OBSERVATION': pred=ty
    else: pred=kalman(ty,tq,c)
    for ep in range(NTEST): rows.append({'train_seed':seed,'condition':c,'episode_id':ep,'policy':f,'episode_mse':float(((pred[ep]-tx[ep])**2).mean()),'episode_mae':float(np.abs(pred[ep]-tx[ep]).mean())})
  print(f'completed training seed {seed}',flush=True)
 with (out/'episode_metrics.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
 with (out/'learned_parameters.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(params[0])); w.writeheader(); w.writerows(params)
 matrices={}; summary={}
 for c in CONDITIONS:
  summary[c]={}
  for p in POLICIES:
   z=[r for r in rows if r['condition']==c and r['policy']==p]; summary[c][p]={'mean_mse':float(np.mean([r['episode_mse'] for r in z])),'mean_mae':float(np.mean([r['episode_mae'] for r in z]))}
  a=np.array([[next(r['episode_mse'] for r in rows if r['train_seed']==s and r['condition']==c and r['episode_id']==e and r['policy']=='GENERIC_RNN_1D')-next(r['episode_mse'] for r in rows if r['train_seed']==s and r['condition']==c and r['episode_id']==e and r['policy']=='MODE_GAIN_FILTER') for e in range(NTEST)] for s in SEEDS]); matrices[c]=a
  summary[c]['primary_contrast']={'generic_minus_mode_mse':float(a.mean()),'positive_seed_means':int((a.mean(1)>0).sum()),'n_seeds':len(SEEDS),'n_episodes':NTEST}
 rng=np.random.default_rng(20261005); a=matrices['ALIGNED']; bs=np.empty(20000)
 for start in range(0,len(bs),128):
  n=min(128,len(bs)-start); si=rng.integers(0,a.shape[0],(n,a.shape[0])); ei=rng.integers(0,a.shape[1],(n,a.shape[1]))
  bs[start:start+n]=a[si[:,:,None],ei[:,None,:]].mean(axis=(1,2))
 summary['ALIGNED']['primary_contrast']['crossed_95_percent_bootstrap_interval']=[float(z) for z in np.quantile(bs,[.025,.975])]
 (out/'summary.json').write_text(json.dumps({'experiment_id':ID,'summary':summary},indent=2)+'\n')
 files=[out/n for n in ('episode_metrics.csv','learned_parameters.csv','summary.json')]; manifest={'experiment_id':ID,'python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'parameters':{'train_seeds':[42000,42019],'training_episodes':NTRAIN,'test_episodes':NTEST,'horizon':T,'updates':UPDATES,'bootstrap_replicates':20000,'bootstrap_seed':20261005},'sha256':{p.name:sha(p) for p in files}}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps(summary,indent=2))
if __name__=='__main__': main()

#!/usr/bin/env python3
"""Cross-dynamics synthetic benchmark of motor-state-conditioned sensory gating."""
import argparse,csv,hashlib,json,platform
from pathlib import Path
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2]; ID='M2_FORWARD_STATE_SENSORY_GATE_V3'
SEEDS=range(42000,42020); NTRAIN=512; NTEST=512; T=160; UPDATES=300; QSW=.05
ENVIRONMENTS=('IN_RANGE','HIGH_PERSISTENCE','LOW_PERSISTENCE')
CONDITIONS=('ALIGNED','INDEPENDENT','REVERSED')
POLICIES=('MODE_GAIN_FILTER','CONSTANT_GAIN_FILTER','GENERIC_RNN_1D','BILINEAR_RNN_1D','GRU_1D','KALMAN_ORACLE')

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def gate(q,c):
 if c=='ALIGNED': return (q>0).astype(np.float32)
 if c=='INDEPENDENT': return np.full(q.shape,.5,np.float32)
 if c=='REVERSED': return (q<0).astype(np.float32)
 raise ValueError(c)
def generate(seed,n,env,condition):
 rng=np.random.default_rng(seed)
 if env=='IN_RANGE': phi=rng.uniform(.84,.96,n); sp=rng.uniform(.08,.18,n); so=rng.uniform(.15,.35,n)
 elif env=='HIGH_PERSISTENCE': phi=np.full(n,.985); sp=np.full(n,.18); so=np.full(n,.25)
 elif env=='LOW_PERSISTENCE': phi=np.full(n,.75); sp=np.full(n,.18); so=np.full(n,.25)
 else: raise ValueError(env)
 x=np.zeros(n,np.float32); q=rng.choice(np.array([-1,1],np.int8),n); xs=[]; qs=[]; ys=[]
 h=gate(q,condition)
 for t in range(T):
  if t:
   x=phi*x+rng.normal(0,sp).astype(np.float32)
   q=np.where(rng.random(n)<QSW,-q,q).astype(np.int8); h=gate(q,condition)
  xs.append(x.copy());qs.append(q.copy());ys.append(h*x+rng.normal(0,so).astype(np.float32))
 return (np.stack(xs,1),np.stack(qs,1),np.stack(ys,1).astype(np.float32),phi.astype(np.float32),sp.astype(np.float32),so.astype(np.float32))
def tensors(y,q,x):return torch.from_numpy(y),torch.from_numpy(q.astype(np.float32)),torch.from_numpy(x)
class Model:
 def __init__(self,f,seed):
  torch.manual_seed(seed); self.f=f
  if f=='GRU_1D':
   self.cell=torch.nn.GRUCell(2,1); self.readout=torch.nn.Linear(1,1)
  else:
   sizes={'MODE_GAIN_FILTER':4,'CONSTANT_GAIN_FILTER':3,'GENERIC_RNN_1D':4,'BILINEAR_RNN_1D':5}
   self.raw=torch.nn.Parameter(torch.tensor({'MODE_GAIN_FILTER':[3,0,0,0],'CONSTANT_GAIN_FILTER':[3,0,0],'GENERIC_RNN_1D':[.5,0,.7,0],'BILINEAR_RNN_1D':[.5,0,0,.7,0]}[f],dtype=torch.float32))
 def parameters(self):
  return list(self.cell.parameters())+list(self.readout.parameters()) if self.f=='GRU_1D' else [self.raw]
 def nparams(self):return sum(p.numel() for p in self.parameters())
 def rollout(self,y,q):
  n,t=y.shape; h=torch.zeros((n,1),dtype=y.dtype) if self.f=='GRU_1D' else torch.zeros(n,dtype=y.dtype); out=[]
  if self.f=='MODE_GAIN_FILTER':
   rho=.999*torch.sigmoid(self.raw[0]); gp=torch.sigmoid(self.raw[1]+self.raw[2]); gm=torch.sigmoid(self.raw[1]-self.raw[2]); b=.2*torch.tanh(self.raw[3])
   for k in range(t):
    p=rho*h; g=torch.where(q[:,k]>0,gp,gm); h=p+g*(y[:,k]-p)+b;out.append(h)
  elif self.f=='CONSTANT_GAIN_FILTER':
   rho=.999*torch.sigmoid(self.raw[0]);g=torch.sigmoid(self.raw[1]);b=.2*torch.tanh(self.raw[2])
   for k in range(t):p=rho*h;h=p+g*(y[:,k]-p)+b;out.append(h)
  elif self.f=='GENERIC_RNN_1D':
   for k in range(t):h=torch.tanh(self.raw[0]*y[:,k]+self.raw[1]*q[:,k]+self.raw[2]*h+self.raw[3]);out.append(h)
  elif self.f=='BILINEAR_RNN_1D':
   for k in range(t):h=torch.tanh(self.raw[0]*y[:,k]+self.raw[1]*q[:,k]+self.raw[2]*y[:,k]*q[:,k]+self.raw[3]*h+self.raw[4]);out.append(h)
  elif self.f=='GRU_1D':
   for k in range(t):h=self.cell(torch.stack([y[:,k],q[:,k]],dim=1),h);out.append(self.readout(h).squeeze(1))
  return torch.stack(out,1)
def train(seed,x,q,y):
 torch.set_num_threads(1); ty,tq,tx=tensors(y,q,x); result={}; curves=[]
 for i,f in enumerate(POLICIES[:-1]):
  m=Model(f,seed+1009*(i+1)); opt=torch.optim.Adam(m.parameters(),lr=.02 if f!='GRU_1D' else .01); first=[];last=[]
  for step in range(UPDATES):
   pred=m.rollout(ty,tq); loss=((pred-tx)**2).mean(); opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
   if step<10:first.append(float(loss.detach()))
   if step>=UPDATES-10:last.append(float(loss.detach()))
  result[f]=m;curves.append({'train_seed':seed,'policy':f,'n_parameters':m.nparams(),'initial_train_mse':float(np.mean(first)),'final_train_mse':float(np.mean(last))})
 return result,curves
def oracle(y,q,phi,sp,so,c):
 n,t=y.shape; state=np.zeros(n); var=np.zeros(n); out=np.empty_like(y)
 for k in range(t):
  if k: var=phi*phi*var+sp*sp;state=phi*state
  h=gate(q[:,k],c); gain=var*h/(h*h*var+so*so); state=state+gain*(y[:,k]-h*state);var=(1-gain*h)*var;out[:,k]=state
 return out.astype(np.float32)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'data/results'/ID);out=ap.parse_args().output_dir.resolve()
 if out.exists() and any(out.iterdir()):raise FileExistsError(out)
 out.mkdir(parents=True,exist_ok=True)
 # Common held-out streams across every training seed and policy.
 evals={}
 for ei,env in enumerate(ENVIRONMENTS):
  base=generate(620000+ei,NTEST,env,'ALIGNED')
  x,q,_,phi,sp,so=base
  evals[env]={c:(x,q,generate(620000+ei,NTEST,env,c)[2],phi,sp,so) for c in CONDITIONS}
 rows=[];params=[];curves=[]
 for seed in SEEDS:
  x,q,y,_,_,_=generate(421000+seed,NTRAIN,'IN_RANGE','ALIGNED');models,curve=train(seed,x,q,y);curves.extend(curve)
  for f,m in models.items():
   raw=m.raw.detach().numpy().tolist() if f!='GRU_1D' else [p.detach().numpy().tolist() for p in m.parameters()]
   params.append({'train_seed':seed,'policy':f,'n_parameters':m.nparams(),'parameters_json':json.dumps(raw)})
  for env in ENVIRONMENTS:
   for c,(x,q,y,phi,sp,so) in evals[env].items():
    for f,m in models.items():
     with torch.no_grad():pred=m.rollout(torch.from_numpy(y),torch.from_numpy(q.astype(np.float32))).numpy()
     for ep in range(NTEST):rows.append({'train_seed':seed,'environment':env,'condition':c,'episode_id':ep,'policy':f,'episode_mse':float(((pred[ep]-x[ep])**2).mean()),'episode_mae':float(np.abs(pred[ep]-x[ep]).mean())})
    pred=oracle(y,q,phi,sp,so,c)
    for ep in range(NTEST):rows.append({'train_seed':seed,'environment':env,'condition':c,'episode_id':ep,'policy':'KALMAN_ORACLE','episode_mse':float(((pred[ep]-x[ep])**2).mean()),'episode_mae':float(np.abs(pred[ep]-x[ep]).mean())})
  print(f'completed training seed {seed}',flush=True)
 for name,rs in [('episode_metrics.csv',rows),('learned_parameters.csv',params),('training_curves.csv',curves)]:
  with (out/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
 import subprocess,sys
 subprocess.run([sys.executable,str(ROOT/'model/M2_FORWARD_STATE_SENSORY_GATE_V3/finalize_results.py')],check=True)
if __name__=='__main__':main()

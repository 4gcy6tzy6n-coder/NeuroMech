#!/usr/bin/env python3
"""Train state estimators and evaluate target approach with endogenous sensor gating."""
import argparse,csv,json,sys
from pathlib import Path
import numpy as np,torch
ROOT=Path(__file__).resolve().parents[2];V3=ROOT/'model/M2_FORWARD_STATE_SENSORY_GATE_V3';sys.path.insert(0,str(V3));import run_experiment as source
ID='M2_CLOSED_LOOP_ACTIVE_SENSING_V1';SEEDS=range(42000,42020);NTRAIN=512;NTEST=512;TTRAIN=64;TTEST=24;UPDATES=250
CONDITIONS=('ALIGNED','INDEPENDENT','REVERSED');POLICIES=('MODE_GAIN_FILTER','CONSTANT_GAIN_FILTER','GENERIC_RNN_1D','BILINEAR_RNN_1D','GRU_1D','BAYESIAN_OBSERVER')
def H(q,c):
 if c=='ALIGNED':return (q>0).astype(np.float32)
 if c=='INDEPENDENT':return np.full(q.shape,.5,np.float32)
 if c=='REVERSED':return (q<0).astype(np.float32)
 raise ValueError(c)
def train_data(seed):
 r=np.random.default_rng(seed);target=r.choice(np.array([-.5,.5],np.float32),NTRAIN);q=np.ones((NTRAIN,TTRAIN),np.int8)
 for t in range(1,TTRAIN):q[:,t]=np.where(r.random(NTRAIN)<.15,-q[:,t-1],q[:,t-1])
 y=H(q,'ALIGNED')*target[:,None]+.35*r.standard_normal((NTRAIN,TTRAIN));return target,q,y.astype(np.float32)
def train(seed,models):
 torch.set_num_threads(1);target,q,y=train_data(431000+seed);tx=torch.from_numpy(y);tq=torch.from_numpy(q.astype(np.float32));truth=torch.from_numpy(np.repeat(target[:,None],TTRAIN,1));curves=[]
 for i,f in enumerate(POLICIES[:-1]):
  m=source.Model(f,seed+1009*(i+1));opt=torch.optim.Adam(m.parameters(),lr=.02 if f!='GRU_1D' else .01);first=[];last=[]
  for step in range(UPDATES):
   loss=((m.rollout(tx,tq)-truth)**2).mean();opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
   if step<10:first.append(float(loss.detach()))
   if step>=UPDATES-10:last.append(float(loss.detach()))
  models[(seed,f)]=m
  raw=m.raw.detach().numpy().tolist() if f!='GRU_1D' else [p.detach().numpy().tolist() for p in m.parameters()]
  curves.append({'train_seed':seed,'policy':f,'n_parameters':m.nparams(),'initial_train_mse':float(np.mean(first)),'final_train_mse':float(np.mean(last)),'parameters_json':json.dumps(raw)})
 return curves
def step_model(m,h,q,y):
 f=m.f;raw=m.raw if f!='GRU_1D' else None
 if f=='MODE_GAIN_FILTER':
  rho=.999*torch.sigmoid(raw[0]);gp=torch.sigmoid(raw[1]+raw[2]);gm=torch.sigmoid(raw[1]-raw[2]);gain=torch.where(q>0,gp,gm);p=rho*h;return p+gain*(y-p)+.2*torch.tanh(raw[3])
 if f=='CONSTANT_GAIN_FILTER':
  rho=.999*torch.sigmoid(raw[0]);gain=torch.sigmoid(raw[1]);p=rho*h;return p+gain*(y-p)+.2*torch.tanh(raw[2])
 if f=='GENERIC_RNN_1D':return torch.tanh(raw[0]*y+raw[1]*q+raw[2]*h+raw[3])
 if f=='BILINEAR_RNN_1D':return torch.tanh(raw[0]*y+raw[1]*q+raw[2]*y*q+raw[3]*h+raw[4])
 new=m.cell(torch.stack([y,q],1),h);return m.readout(new).squeeze(1)
def oracle_step(mean,var,logodds,q,y,c):
 hc=torch.from_numpy(H(q.numpy(),c));logodds=logodds+2*.5*hc*y/(.35**2);mean=.5*torch.tanh(logodds/2);return mean,logodds
def episode_eval(theta,noise,m,c):
 n=len(theta);dev=torch.device('cpu');target=torch.from_numpy(theta);p=torch.zeros(n);q=torch.ones(n);h=torch.zeros((n,1)) if m.f=='GRU_1D' else torch.zeros(n);logodds=torch.zeros(n);dist=[]
 for t in range(TTEST):
  hc=torch.from_numpy(H(q.numpy(),c));y=hc*target+.35*torch.from_numpy(noise[:,t]);
  if m.f=='BAYESIAN_OBSERVER':estimate,logodds=oracle_step(None,None,logodds,q,y,c)
  else:estimate=step_model(m,h,q,y);h=estimate if m.f!='GRU_1D' else m.cell(torch.stack([y,q],1),h)
  # For the GRU readout, preserve its hidden state and use the readout value above.
  delta=estimate-p;action=torch.where(delta>.025,torch.ones_like(q),torch.where(delta<-.025,-torch.ones_like(q),torch.zeros_like(q)))
  move=action*.05;p=p+move;dist.append(torch.abs(target-p).numpy())
  q=torch.where(action==0,q,action)
 return np.stack(dist,1)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'data/results'/ID);out=ap.parse_args().output_dir.resolve()
 if out.exists() and any(out.iterdir()):raise FileExistsError(out)
 torch.set_num_threads(1);out.mkdir(parents=True,exist_ok=True);models={};curves=[];params=[]
 for seed in SEEDS:
  curves.extend(train(seed,models));print(f'trained seed {seed}',flush=True)
 for seed in SEEDS:
  for f in POLICIES[:-1]:
   m=models[(seed,f)];raw=m.raw.detach().numpy().tolist() if f!='GRU_1D' else [p.detach().numpy().tolist() for p in m.parameters()];params.append({'train_seed':seed,'policy':f,'n_parameters':m.nparams(),'parameters_json':json.dumps(raw)})
 rows=[]
 for condition_i,c in enumerate(CONDITIONS):
  rng=np.random.default_rng(650000);theta=rng.choice(np.array([-.5,.5],np.float32),NTEST);noise=rng.standard_normal((NTEST,TTEST)).astype(np.float32)
  for seed in SEEDS:
   for f in POLICIES[:-1]:
    m=models[(seed,f)];m.eval() if hasattr(m,'eval') else None
    with torch.no_grad():d=episode_eval(theta,noise,m,c)
    for ep in range(NTEST):rows.append({'train_seed':seed,'condition':c,'episode_id':ep,'policy':f,'mean_distance':float(d[ep].mean()),'terminal_distance':float(d[ep,-1]),'success':int(d[ep,-1]<=.10)})
   # Bayesian observer uses the same greedy controller as learned estimators.
   oracle=source.Model('CONSTANT_GAIN_FILTER',seed);oracle.f='BAYESIAN_OBSERVER'
   with torch.no_grad():d=episode_eval(theta,noise,oracle,c)
   for ep in range(NTEST):rows.append({'train_seed':seed,'condition':c,'episode_id':ep,'policy':'BAYESIAN_OBSERVER','mean_distance':float(d[ep].mean()),'terminal_distance':float(d[ep,-1]),'success':int(d[ep,-1]<=.10)})
  print(f'evaluated closed-loop condition {c}',flush=True)
 for name,rs in [('episode_control.csv',rows),('learned_parameters.csv',params),('training_curves.csv',curves)]:
  with (out/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
 import subprocess
 subprocess.run([sys.executable,str(ROOT/'model/M2_CLOSED_LOOP_ACTIVE_SENSING_V1/finalize_results.py')],check=True)
if __name__=='__main__':main()

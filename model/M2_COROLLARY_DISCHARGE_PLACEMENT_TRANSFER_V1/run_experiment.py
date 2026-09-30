#!/usr/bin/env python3
"""Test sensory-site motor feedback against output persistence and controls."""
from __future__ import annotations
import argparse,csv,hashlib,json,platform,time
from pathlib import Path
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2];EXP='M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1'
CONTRACT=ROOT/'summery'/EXP/'CONTRACT.md';SEEDS=range(88000,88030)
HAZARDS=(.01,.05,.20);ARMS=('SENSORY_SITE_CD','OUTPUT_SITE_PERSISTENCE','NO_FEEDBACK','GENERIC_RNN_2H','BAYES_FILTER')
NTRAIN=256;TTRAIN=256;NTEST=512;TTEST=512;UPDATES=200;BATCH=16;NOISE=1.25;LR=.01

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def gen_sequences(rng,n,t,hazard):
    states=np.empty((n,t),np.float32);states[:,0]=rng.choice(np.array([-1.,1.],np.float32),n)
    flips=rng.random((n,t-1))<hazard
    for k in range(1,t):states[:,k]=np.where(flips[:,k-1],-states[:,k-1],states[:,k-1])
    obs=states+rng.normal(0,NOISE,(n,t)).astype(np.float32)
    return states,obs

class Minimal(torch.nn.Module):
    def __init__(self,kind,seed):
        super().__init__();self.kind=kind;torch.manual_seed(seed)
        self.raw=torch.nn.Parameter(torch.tensor([3.0,.5,.1],dtype=torch.float32))
        if kind=='NO_FEEDBACK':
            with torch.no_grad():self.raw[2]=0.0
    def sequence(self,x):
        batch,t=x.shape;h=torch.zeros(batch,dtype=x.dtype);ap=torch.zeros_like(h);logits=[]
        rho=.99*torch.sigmoid(self.raw[0]);alpha=self.raw[1];beta=self.raw[2]
        for k in range(t):
            if self.kind=='SENSORY_SITE_CD':
                h=torch.tanh(rho*h+alpha*x[:,k]+beta*ap);logit=h
            elif self.kind=='OUTPUT_SITE_PERSISTENCE':
                h=torch.tanh(rho*h+alpha*x[:,k]);logit=h+beta*ap
            elif self.kind=='NO_FEEDBACK':
                h=torch.tanh(rho*h+alpha*x[:,k]+beta);logit=h
            else:raise ValueError(self.kind)
            logits.append(logit);ap=torch.where(logit.detach()>=0,1.,-1.)
        return torch.stack(logits,dim=1)

class GenericRNN(torch.nn.Module):
    def __init__(self,seed):
        super().__init__();torch.manual_seed(seed)
        self.wh=torch.nn.Parameter(torch.eye(2)*.25);self.wx=torch.nn.Parameter(torch.tensor([.5,.1]));self.wa=torch.nn.Parameter(torch.tensor([.1,.1]));self.bias=torch.nn.Parameter(torch.zeros(2));self.readout=torch.nn.Parameter(torch.tensor([1.,.1]));self.out_bias=torch.nn.Parameter(torch.zeros(()))
    def sequence(self,x):
        batch,t=x.shape;h=torch.zeros(batch,2,dtype=x.dtype);ap=torch.zeros(batch,dtype=x.dtype);logits=[]
        for k in range(t):
            h=torch.tanh(h@self.wh.T+x[:,k,None]*self.wx+ap[:,None]*self.wa+self.bias)
            logit=h@self.readout+self.out_bias;logits.append(logit);ap=torch.where(logit.detach()>=0,1.,-1.)
        return torch.stack(logits,dim=1)

def train_one(kind,seed,states,obs):
    model=GenericRNN(seed+4409) if kind=='GENERIC_RNN_2H' else Minimal(kind,seed+4409)
    opt=torch.optim.Adam(model.parameters(),lr=LR);rng=np.random.default_rng(np.random.SeedSequence([seed,900+ARMS.index(kind)]));tx=torch.from_numpy(obs);ty=torch.from_numpy((states+1.)/2.);losses=[];start=time.perf_counter()
    for _ in range(UPDATES):
        ix=torch.from_numpy(rng.integers(0,NTRAIN,BATCH));logit=model.sequence(tx[ix]);loss=torch.nn.functional.binary_cross_entropy_with_logits(logit,ty[ix]);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.);opt.step();losses.append(float(loss.detach()))
    flat=torch.cat([p.detach().reshape(-1) for p in model.parameters()]).numpy().tolist()
    return model,{'training_seed':seed,'arm':kind,'parameter_count':sum(p.numel() for p in model.parameters()),'updates':UPDATES,'batch_size':BATCH,'initial_loss':losses[0],'final_10_update_loss':float(np.mean(losses[-10:])),'training_seconds':time.perf_counter()-start,'parameters_json':json.dumps(flat)}

def bayes_decisions(obs,hazard):
    n,t=obs.shape;p=np.full(n,.5,np.float64);acts=np.empty((n,t),np.float32)
    for k in range(t):
        if k:p=(1-hazard)*p+hazard*(1-p)
        logodds=np.log(p/(1-p))+2*obs[:,k]/(NOISE**2);p=1/(1+np.exp(-np.clip(logodds,-40,40)));acts[:,k]=np.where(p>=.5,1.,-1.)
    return acts

def episode_metrics(states,actions):
    correct=actions==states;switched_s=states[:,1:]!=states[:,:-1];switched_a=actions[:,1:]!=actions[:,:-1]
    false_num=np.logical_and(switched_a,~switched_s).sum(axis=1);false_den=np.maximum((~switched_s).sum(axis=1),1)
    lag=np.full(len(states),np.nan,np.float64)
    for i in range(len(states)):
        changes=np.flatnonzero(switched_s[i])+1
        if len(changes):
            vals=[]
            for t in changes:
                idx=np.flatnonzero(actions[i,t:min(t+16,actions.shape[1])]==states[i,t:min(t+16,states.shape[1])])
                vals.append(float(idx[0]) if len(idx) else 16.)
            lag[i]=float(np.mean(vals))
    return correct.mean(axis=1),false_num/false_den,lag

def write_csv(path,rows):
    with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'data/results'/EXP/'canonical');a=ap.parse_args();out=a.output_dir.resolve()
    if out.exists() and any(out.iterdir()):raise FileExistsError(f'refusing to overwrite {out}')
    out.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1);rows=[];fits=[]
    for si,seed in enumerate(SEEDS):
        rng=np.random.default_rng(np.random.SeedSequence([seed,11]));tr_s,tr_x=gen_sequences(rng,NTRAIN,TTRAIN,.05);trained={}
        for arm in ARMS[:-1]:
            model,fit=train_one(arm,seed,*[tr_s,tr_x]);trained[arm]=model;fits.append(fit)
        for hi,hazard in enumerate(HAZARDS):
            te_rng=np.random.default_rng(np.random.SeedSequence([seed,30+hi]));te_s,te_x=gen_sequences(te_rng,NTEST,TTEST,hazard)
            for arm in ARMS:
                if arm=='BAYES_FILTER':act=bayes_decisions(te_x,hazard)
                else:
                    with torch.no_grad():log=trained[arm].sequence(torch.from_numpy(te_x)).numpy()
                    act=np.where(log>=0,1.,-1.).astype(np.float32)
                acc,false,lag=episode_metrics(te_s,act)
                for ep in range(NTEST):rows.append({'training_seed':seed,'hazard':hazard,'episode_id':ep,'arm':arm,'accuracy':float(acc[ep]),'false_action_switch_rate':float(false[ep]),'switch_recovery_lag':float(lag[ep]) if np.isfinite(lag[ep]) else ''})
        print(f'completed corollary-discharge seed {seed} ({si+1}/{len(SEEDS)})',flush=True)
    write_csv(out/'episode_metrics.csv',rows);write_csv(out/'training_metrics.csv',fits)
    man={'experiment_id':EXP,'classification':'post-result exploratory artificial mechanism-transfer study','python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'training_seeds':[SEEDS.start,SEEDS.stop-1],'train_hazard':.05,'test_hazards':HAZARDS,'n_train':NTRAIN,'train_steps':TTRAIN,'n_test':NTEST,'test_steps':TTEST,'updates':UPDATES,'batch_size':BATCH,'learning_rate':LR,'observation_noise_sd':NOISE,'arms':ARMS,'rows':len(rows),'runner_sha256':sha(Path(__file__)),'contract_sha256':sha(CONTRACT),'files':{}}
    for name in ('episode_metrics.csv','training_metrics.csv'):man['files'][name]=sha(out/name)
    (out/'run_manifest.json').write_text(json.dumps(man,indent=2)+'\n');print(json.dumps(man,indent=2))
if __name__=='__main__':main()

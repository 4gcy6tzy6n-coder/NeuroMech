#!/usr/bin/env python3
"""Post-result training-distribution diagnostic for 2D closed-loop pursuit."""
from __future__ import annotations
import argparse,csv,hashlib,json,platform,time
from pathlib import Path
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2]
EXP='M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC'
CONTRACT=ROOT/'summery'/EXP/'CONTRACT.md'
SEEDS=range(76000,76030)
REGIMES=('RANDOM_ACTION','TEACHER_MIXED_CLOSED_LOOP')
ARMS=('MODE_GAIN','NO_CONTEXT','ADDITIVE_RNN_MATCHED','BILINEAR_RNN_MATCHED','KALMAN_ORACLE')
CONDS=('ALIGNED','REVERSED')
NTRAIN=512;NTEST=256;T=32;UPDATES=200;BATCH=16;STEP=.12;NOISE=.25;SUCCESS_RADIUS=.12;TEACHER_RANDOM_P=.25

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def sensor_matrix(q,condition):
    aligned=(condition=='ALIGNED');horizontal_high=(q>0) if aligned else (q<0)
    if np.ndim(horizontal_high)>0:return np.where(np.asarray(horizontal_high)[:,None],np.array([.95,.10],np.float32),np.array([.10,.95],np.float32))
    return np.array([.95,.10],np.float32) if horizontal_high else np.array([.10,.95],np.float32)

def oracle_update(mean,var,y,pos,q):
    h=sensor_matrix(q,'ALIGNED');den=h*h*var+NOISE**2;k=var*h/den;z=y+h*pos
    return mean+k*(z-h*mean),(1-k*h)*var

def generate_training(regime,targets,innovations,seed):
    rng=np.random.default_rng(np.random.SeedSequence([seed,731]))
    pos=np.zeros_like(targets);obs=np.empty((NTRAIN,T,2),np.float32);qseq=np.empty((NTRAIN,T),np.float32)
    dseq=np.zeros((NTRAIN,T,2),np.float32);labels=np.empty_like(obs)
    belief=np.zeros_like(targets);var=np.full_like(targets,.25);q=np.ones(NTRAIN,np.float32)
    for t in range(T):
        h=sensor_matrix(q,'ALIGNED');y=h*(targets-pos)+innovations[:,t]
        obs[:,t]=y;qseq[:,t]=q;labels[:,t]=targets-pos
        if t==T-1:break
        if regime=='TEACHER_MIXED_CLOSED_LOOP':
            belief,var=oracle_update(belief,var,y,pos,q)
            estimate=belief-pos
            greedy_axis=np.argmax(np.abs(estimate),axis=1)
            greedy_sign=np.sign(estimate[np.arange(NTRAIN),greedy_axis]);greedy_sign[greedy_sign==0]=1
            exploratory=rng.random(NTRAIN)<TEACHER_RANDOM_P
            axis=np.where(exploratory,rng.integers(0,2,NTRAIN),greedy_axis)
            direction=np.where(exploratory,rng.choice(np.array([-1.,1.]),NTRAIN),greedy_sign)
        elif regime=='RANDOM_ACTION':
            axis=rng.integers(0,2,NTRAIN);direction=rng.choice(np.array([-1.,1.]),NTRAIN)
        else:raise ValueError(regime)
        delta=np.zeros_like(pos);delta[np.arange(NTRAIN),axis]=direction*STEP
        pos+=delta;dseq[:,t+1]=delta;q=np.where(axis==0,1.,-1.).astype(np.float32)
    return obs,qseq,dseq,labels

class Model:
    def __init__(self,name,seed):
        self.name=name;torch.manual_seed(seed)
        init={'MODE_GAIN':[5.,5.,-.174,-.174,1.56,-1.56,0.,0.], 'NO_CONTEXT':[5.,5.,0.,0.,0.,0.], 'ADDITIVE_RNN_MATCHED':[3.,3.,.5,.5,0.,0.,0.,0.], 'BILINEAR_RNN_MATCHED':[3.,3.,.5,.5,0.,0.,0.,0.]}[name]
        self.raw=torch.nn.Parameter(torch.tensor(init,dtype=torch.float32))
    def parameters(self):return [self.raw]
    def step(self,h,y,q,delta):
        prior=h-delta
        if self.name=='MODE_GAIN':
            rho=.999*torch.sigmoid(self.raw[:2]);g=torch.sigmoid(self.raw[2:4]+self.raw[4:6]*q[:,None]);return rho*prior+g*(y-prior)+self.raw[6:8]
        if self.name=='NO_CONTEXT':
            rho=.999*torch.sigmoid(self.raw[:2]);g=torch.sigmoid(self.raw[2:4]);return rho*prior+g*(y-prior)+self.raw[4:6]
        rho=.999*torch.sigmoid(self.raw[:2]);ay=self.raw[2:4];bias=self.raw[6:8]
        if self.name=='ADDITIVE_RNN_MATCHED':return rho*prior+ay*y+self.raw[4:6]*q[:,None]+bias
        return rho*prior+ay*y+self.raw[4:6]*(y*q[:,None])+bias
    def rollout(self,y,q,delta):
        h=torch.zeros((y.shape[0],2),dtype=y.dtype);out=[]
        for t in range(y.shape[1]):h=self.step(h,y[:,t],q[:,t],delta[:,t]);out.append(h)
        return torch.stack(out,dim=1)

def train_one(name,seed,obs,q,delta,labels,regime):
    m=Model(name,seed+1009*(('MODE_GAIN','NO_CONTEXT','ADDITIVE_RNN_MATCHED','BILINEAR_RNN_MATCHED').index(name)+1))
    opt=torch.optim.Adam(m.parameters(),lr=.02);rng=np.random.default_rng(11000000+seed*103);to=torch.from_numpy
    ty,tq,td,tl=map(to,(obs,q,delta,labels));losses=[];start=time.perf_counter()
    for _ in range(UPDATES):
        ix=torch.from_numpy(rng.integers(0,NTRAIN,BATCH));pred=m.rollout(ty[ix],tq[ix],td[ix]);loss=((pred-tl[ix])**2).mean();opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step();losses.append(float(loss.detach()))
    return m,{'training_seed':seed,'regime':regime,'arm':name,'parameter_count':m.raw.numel(),'updates':UPDATES,'batch_size':BATCH,'training_seconds':time.perf_counter()-start,'initial_loss':losses[0],'final_10_update_loss':float(np.mean(losses[-10:])),'parameters_json':json.dumps(m.raw.detach().numpy().tolist())}

def evaluate(model,target,noise,condition):
    n=len(target);pos=np.zeros((n,2),np.float32);hstate=np.zeros((n,2),np.float32);q=np.ones(n,np.float32);delta=np.zeros_like(pos)
    belief=np.zeros_like(pos);var=np.full_like(pos,.25);active=np.ones(n,bool);distances=np.zeros((n,T),np.float32);steps=np.full(n,T,np.int16)
    for t in range(T):
        gains=sensor_matrix(q,condition);y=gains*(target-pos)+noise[:,t]
        if model=='KALMAN_ORACLE':
            mnew,vnew=oracle_eval_update(belief.astype(float),var.astype(float),y.astype(float),pos.astype(float),q.astype(float),condition);belief=mnew.astype(np.float32);var=vnew.astype(np.float32);estimate=belief-pos
        else:
            with torch.no_grad():hstate=model.step(torch.from_numpy(hstate),torch.from_numpy(y),torch.from_numpy(q),torch.from_numpy(delta)).numpy()
            estimate=hstate
        distance=np.linalg.norm(target-pos,axis=1);distances[:,t]=distance
        reached=active&(distance<=SUCCESS_RADIUS);steps[reached]=t+1;active[reached]=False
        if t==T-1:break
        move=np.zeros_like(pos);axis=np.argmax(np.abs(estimate),axis=1);idx=np.where(active)[0];sg=np.sign(estimate[idx,axis[idx]]);sg[sg==0]=1;move[idx,axis[idx]]=STEP*sg
        pos+=move;delta=move;q=np.where(axis==0,1.,-1.).astype(np.float32);delta[~active]=0
    final=np.linalg.norm(target-pos,axis=1);return final,(final<=SUCCESS_RADIUS).astype(np.int8),distances.mean(axis=1),steps

def oracle_eval_update(mean,var,y,pos,q,condition):
    h=sensor_matrix(q,condition);den=h*h*var+NOISE**2;k=var*h/den;z=y+h*pos
    return mean+k*(z-h*mean),(1-k*h)*var

def write(path,rows):
    with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'data/results'/EXP/'canonical');a=ap.parse_args();out=a.output_dir.resolve()
    if out.exists() and any(out.iterdir()):raise FileExistsError(f'refusing to overwrite {out}')
    out.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1);rows=[];fits=[]
    for si,seed in enumerate(SEEDS):
        data_rng=np.random.default_rng(np.random.SeedSequence([seed,101]));targets=data_rng.normal(0,.5,(NTRAIN,2)).astype(np.float32);innov=data_rng.normal(0,NOISE,(NTRAIN,T,2)).astype(np.float32)
        test_rng=np.random.default_rng(np.random.SeedSequence([seed,202]));test_targets=test_rng.normal(0,.5,(NTEST,2)).astype(np.float32);test_noise=test_rng.normal(0,NOISE,(NTEST,T,2)).astype(np.float32)
        for regime in REGIMES:
            tr=generate_training(regime,targets,innov,seed);trained={}
            for arm in ARMS[:-1]:
                model,fit=train_one(arm,seed,*tr,regime);trained[arm]=model;fits.append(fit)
            for condition in CONDS:
                for arm in ARMS:
                    obj='KALMAN_ORACLE' if arm=='KALMAN_ORACLE' else trained[arm]
                    final,success,avgdist,steps=evaluate(obj,test_targets,test_noise,condition)
                    for ep in range(NTEST):rows.append({'training_seed':seed,'regime':regime,'condition':condition,'episode_id':ep,'arm':arm,'final_distance':float(final[ep]),'success':int(success[ep]),'mean_distance':float(avgdist[ep]),'steps_to_success':int(steps[ep])})
        print(f'completed diagnostic seed {seed} ({si+1}/{len(SEEDS)})',flush=True)
    write(out/'episode_metrics.csv',rows);write(out/'training_metrics.csv',fits)
    man={'experiment_id':EXP,'classification':'post-result exploratory training-distribution diagnostic','python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'training_seeds':[SEEDS.start,SEEDS.stop-1],'n_train':NTRAIN,'n_test':NTEST,'steps':T,'updates':UPDATES,'batch_size':BATCH,'movement_step':STEP,'noise_sd':NOISE,'teacher_random_action_probability':TEACHER_RANDOM_P,'regimes':REGIMES,'arms':ARMS,'conditions':CONDS,'rows':len(rows),'runner_sha256':sha(Path(__file__)),'contract_sha256':sha(CONTRACT),'files':{}}
    for name in ('episode_metrics.csv','training_metrics.csv'):man['files'][name]=sha(out/name)
    (out/'run_manifest.json').write_text(json.dumps(man,indent=2)+'\n');print(json.dumps(man,indent=2))

if __name__=='__main__':main()

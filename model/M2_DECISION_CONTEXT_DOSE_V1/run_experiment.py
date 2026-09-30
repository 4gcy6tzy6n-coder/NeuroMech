#!/usr/bin/env python3
"""Test transfer of the M2 context-information dose curve to terminal decisions."""
from __future__ import annotations
import argparse,csv,hashlib,json,platform,time
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[2]; EXP="M2_DECISION_CONTEXT_DOSE_V1"
SEEDS=range(74000,74030); SIZES=(64,256,1024); KAPPAS=np.round(np.arange(-.5,.5001,.1),2)
LEARNED=("MODE_GAIN_FILTER","CONSTANT_GAIN_FILTER","LINEAR_BILINEAR_RNN"); ARMS=LEARNED+("BAYES_ORACLE",)
T=32; NTEST=256; UPDATES=250; BATCH=16; MU=.18; NOISE=.7; QSWITCH=.25; BOOT=10000; BOOT_SEED=20261017
CONTRACT=ROOT/"summery"/EXP/"CONTRACT.md"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def generate(seed,n):
    rng=np.random.default_rng(seed); target=rng.choice(np.array([-1.,1.],np.float32),n);q=np.empty((n,T),np.float32);q[:,0]=rng.choice(np.array([-1.,1.],np.float32),n)
    flips=rng.random((n,T))<QSWITCH;noise=rng.standard_normal((n,T)).astype(np.float32)
    for t in range(1,T):q[:,t]=np.where(flips[:,t],-q[:,t-1],q[:,t-1])
    return target,q,noise
def obs(target,q,noise,k):return ((.5+np.float32(k)*q)*MU*target[:,None]+NOISE*noise).astype(np.float32)
class Model:
    def __init__(self,arm):
        self.arm=arm;init={"MODE_GAIN_FILTER":[2.5,0.,0.,0.],"CONSTANT_GAIN_FILTER":[2.5,0.,0.],"LINEAR_BILINEAR_RNN":[.1,0.,.1,.4,0.]}[arm];self.raw=torch.nn.Parameter(torch.tensor(init,dtype=torch.float32))
    def parameters(self):return [self.raw]
    def rollout(self,y,q):
        h=torch.zeros(y.shape[0],dtype=y.dtype);out=[]
        if self.arm=="MODE_GAIN_FILTER":
            rho=.999*torch.sigmoid(self.raw[0]);gp=torch.sigmoid(self.raw[1]+self.raw[2]);gm=torch.sigmoid(self.raw[1]-self.raw[2]);bias=.2*torch.tanh(self.raw[3])
            for t in range(y.shape[1]):p=rho*h;g=torch.where(q[:,t]>0,gp,gm);h=p+g*(y[:,t]-p)+bias;out.append(h)
        elif self.arm=="CONSTANT_GAIN_FILTER":
            rho=.999*torch.sigmoid(self.raw[0]);g=torch.sigmoid(self.raw[1]);bias=.2*torch.tanh(self.raw[2])
            for t in range(y.shape[1]):p=rho*h;h=p+g*(y[:,t]-p)+bias;out.append(h)
        else:
            wy,wq,wyq=.5*torch.tanh(self.raw[:3]);wh,whq=.4*torch.tanh(self.raw[3]),.4*torch.tanh(self.raw[4])
            for t in range(y.shape[1]):h=wy*y[:,t]+wq*q[:,t]+wyq*y[:,t]*q[:,t]+wh*h+whq*q[:,t]*h;out.append(h)
        return torch.stack(out,dim=1)
def bayes(y,q,k):
    h=.5+k*q;logodds=np.sum((2*MU/NOISE**2)*h*y,axis=1);return np.tanh(.5*logodds).astype(np.float32)
def metrics(pred,target):
    label=target>0;p=np.clip((pred+1)*.5,0,1);return ((pred>=0)==label).astype(np.int8),(pred-target)**2,(p-label.astype(np.float32))**2
def write(path,rows):
    with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'data/results'/EXP/'canonical');a=ap.parse_args();out=a.output_dir.resolve()
    if out.exists() and any(out.iterdir()):raise FileExistsError(f'refusing to overwrite {out}')
    out.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1);rows=[];fits=[]
    for si,seed in enumerate(SEEDS):
        pool_s,pool_q,pool_n=generate(seed*41+39,max(SIZES));test_s,test_q,test_n=generate(960000+seed,NTEST)
        for ni,ntrain in enumerate(SIZES):
            tr_y=obs(pool_s[:ntrain],pool_q[:ntrain],pool_n[:ntrain],.5);ty=torch.from_numpy(tr_y);tq=torch.from_numpy(pool_q[:ntrain]);ts=torch.from_numpy(pool_s[:ntrain])
            for ai,arm in enumerate(LEARNED):
                torch.manual_seed(seed+1009*(ai+1)+ni*101);m=Model(arm);opt=torch.optim.Adam(m.parameters(),lr=.02);rng=np.random.default_rng(11000000+seed*103+ni*13);losses=[];start=time.perf_counter()
                for _ in range(UPDATES):
                    ix=torch.from_numpy(rng.integers(0,ntrain,size=BATCH));pred=m.rollout(ty[ix],tq[ix]);loss=((pred-ts[ix,None])**2).mean();opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step();losses.append(float(loss.detach()))
                fits.append({'training_seed':seed,'train_size':ntrain,'arm':arm,'parameter_count':m.raw.numel(),'updates':UPDATES,'batch_size':BATCH,'sample_tokens':UPDATES*BATCH*T,'training_seconds':time.perf_counter()-start,'initial_loss':losses[0],'final_10_update_loss':float(np.mean(losses[-10:])),'parameters_json':json.dumps(m.raw.detach().numpy().tolist())})
                for k in KAPPAS:
                    y=obs(test_s,test_q,test_n,float(k));
                    with torch.no_grad():outcome=m.rollout(torch.from_numpy(y),torch.from_numpy(test_q)).numpy()[:,-1]
                    corr,mse,brier=metrics(outcome,test_s)
                    for ep in range(NTEST):rows.append({'training_seed':seed,'train_size':ntrain,'kappa':f'{k:.2f}','episode_id':ep,'arm':arm,'correct':int(corr[ep]),'terminal_mse':float(mse[ep]),'brier':float(brier[ep])})
            for k in KAPPAS:
                y=obs(test_s,test_q,test_n,float(k));p=bayes(y,test_q,float(k));corr,mse,brier=metrics(p,test_s)
                for ep in range(NTEST):rows.append({'training_seed':seed,'train_size':ntrain,'kappa':f'{k:.2f}','episode_id':ep,'arm':'BAYES_ORACLE','correct':int(corr[ep]),'terminal_mse':float(mse[ep]),'brier':float(brier[ep])})
        print(f'completed decision seed {seed} ({si+1}/{len(SEEDS)})',flush=True)
    write(out/'episode_metrics.csv',rows);write(out/'training_metrics.csv',fits)
    man={'experiment_id':EXP,'classification':'exploratory artificial objective-transfer study','python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'training_seeds':[SEEDS.start,SEEDS.stop-1],'training_stream_rule':'seed*41+39','test_stream_rule':'960000+seed','train_sizes':SIZES,'n_test':NTEST,'steps':T,'updates':UPDATES,'batch_size':BATCH,'kappas':[float(k) for k in KAPPAS],'arms':ARMS,'rows':len(rows),'runner_sha256':sha(Path(__file__)),'contract_sha256':sha(CONTRACT),'files':{}}
    for name in ('episode_metrics.csv','training_metrics.csv'):man['files'][name]=sha(out/name)
    (out/'run_manifest.json').write_text(json.dumps(man,indent=2)+'\n');print(json.dumps(man,indent=2))
if __name__=='__main__':main()

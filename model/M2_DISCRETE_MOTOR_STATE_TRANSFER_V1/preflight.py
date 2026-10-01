import numpy as np, torch
from torch import nn

torch.set_num_threads(1)
T=64; B=32; UPDATES=160; LR=.003
RHO=.6; GAIN=.4; MNOISE=.025; ONOISE=.14

def batch(seed,n,alpha=.93,missfrac=.5,burst=8):
 r=np.random.default_rng(seed)
 if alpha is None: alpha=r.uniform(.84,.97,n)
 target=np.zeros((n,T),np.float32); target[:,0]=r.uniform(-1,1,n)
 v=r.normal(0,.055,n).astype(np.float32)
 for t in range(1,T):
  v=alpha*v+r.normal(0,.055,n);target[:,t]=target[:,t-1]+v
 mn=r.normal(0,MNOISE,(n,T)).astype(np.float32); on=r.normal(0,ONOISE,(n,T)).astype(np.float32)
 av=np.ones((n,T),bool); p_leave=1/burst; p_enter=missfrac/(1-missfrac)*p_leave
 m=r.random(n)<missfrac
 for t in range(T):
  if t: 
   u=r.random(n);m=np.where(m,u>=p_leave,u<p_enter)
  av[:,t]=~m
 return target,mn,on,av
class C(nn.Module):
 def __init__(self,seed):
  super().__init__();torch.manual_seed(seed);self.cell=nn.GRUCell(3,8);self.out=nn.Linear(8,1)
 def step(self,x,h):
  h=self.cell(x,h);return torch.tanh(self.out(h)).squeeze(-1),h

def rollout(model, arm, dat, yoke=None):
 target,mn,on,av=dat;n=len(target); yoke=torch.from_numpy(yoke) if isinstance(yoke,np.ndarray) else yoke; pos=torch.zeros(n);vel=torch.zeros(n);pc=torch.zeros(n);h=torch.zeros(n,8);err=[];vsign=[]
 with torch.no_grad():
  for t in range(T):
   vel=RHO*vel+GAIN*pc+torch.from_numpy(mn[:,t]);pos=pos+vel;rel=torch.from_numpy(target[:,t])-pos
   obs=torch.where(torch.from_numpy(av[:,t]),rel+torch.from_numpy(on[:,t]),torch.zeros(n))
   sig=torch.where(vel>=0,1.,-1.)
   if arm=='self':fb=sig
   elif arm=='zero':fb=torch.zeros(n)
   elif arm=='action':fb=torch.where(pc>=0,1.,-1.)
   elif arm=='yoke':fb=yoke[:,t]
   x=torch.stack((obs,torch.from_numpy(av[:,t]).float(),fb),-1);cmd,h=model.step(x,h)
   err.append(rel.square());vsign.append(sig);pc=cmd
 return torch.stack(err,1).mean(1).numpy(), np.stack([x.numpy() for x in vsign],1)

def train(seed, arm, dat, donor=None):
 model=C(seed+1901); opt=torch.optim.Adam(model.parameters(),lr=LR);target,mn,on,av=dat
 for u in range(UPDATES):
  d=batch(seed+100000+u*7919,B,alpha=None,missfrac=.5,burst=4)
  yoke=None
  if arm=='yoke':
   _,drive=rollout(donor,'self',d)
   ix=np.random.default_rng(seed+u+333).permutation(B)
   if np.any(ix==np.arange(B)): # derangement via roll
    ix=np.roll(np.arange(B),1)
   yoke=torch.from_numpy(drive[ix])
  tar=torch.from_numpy(d[0]);m=torch.from_numpy(d[1]);o=torch.from_numpy(d[2]);a=torch.from_numpy(d[3]);n=B
  pos=torch.zeros(n);vel=torch.zeros(n);pc=torch.zeros(n);h=torch.zeros(n,8);loss=[]
  for t in range(T):
   vel=RHO*vel+GAIN*pc+m[:,t];pos+=vel;rel=tar[:,t]-pos
   obs=torch.where(a[:,t],rel+o[:,t],torch.zeros(n)); sig=torch.where(vel>=0,1.,-1.)
   if arm=='self':fb=sig
   elif arm=='zero':fb=torch.zeros(n)
   elif arm=='action':fb=torch.where(pc>=0,1.,-1.)
   elif arm=='yoke':fb=yoke[:,t]
   x=torch.stack((obs,a[:,t].float(),fb),-1);cmd,h=model.step(x,h)
   loss.append(rel.square()+.002*cmd.square());pc=cmd
  L=torch.stack(loss,1).mean();opt.zero_grad();L.backward();nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
 return model

allres=[]
for s in range(6):
 d=batch(900000+s*1000,256,missfrac=.5,burst=8);dt=tuple(torch.from_numpy(a) for a in d)
 models={}
 models['self']=train(5000+s,'self',dt)
 models['zero']=train(5000+s,'zero',dt)
 models['action']=train(5000+s,'action',dt)
 models['yoke']=train(5000+s,'yoke',dt,models['self'])
 # train-like shaped heldout long burst
 _,test_drive=rollout(models['self'],'self',d)
 for k,m in models.items():
  yk=test_drive[np.roll(np.arange(len(test_drive)),1)] if k=='yoke' else None
  x,_=rollout(m,k,d,yk);allres.append((s,k,float(x.mean())))
 # reactive controller and oracle-ish access only for task adequacy
 tar,mn,on,av=d;pos=np.zeros(256);vel=np.zeros(256);pc=np.zeros(256);es=[]
 for t in range(T):
  vel=RHO*vel+GAIN*pc+mn[:,t];pos+=vel;rel=tar[:,t]-pos
  obs=np.where(av[:,t],rel+on[:,t],0);cmd=np.where(av[:,t],np.clip(.55*obs,-1,1),0);es.append(rel**2);pc=cmd
 print('seed',s,'means', {k:round(np.mean([x[2] for x in allres if x[0]==s and x[1]==k]),4) for k in models},'reactive',round(np.mean(es),4),flush=True)
print(allres)

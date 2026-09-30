#!/usr/bin/env python3
"""Post-result V2: learnable short-delay temporal XOR with local eligibility updates."""
from __future__ import annotations
import csv, hashlib, json, math, platform
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/results/M5_ELIGIBILITY_TEMPORAL_XOR_V2'
CONTRACT=ROOT/'summery/M5_ELIGIBILITY_TEMPORAL_XOR_V2/CONTRACT.md'
SEEDS=tuple(range(1000,1030)); DELAY=4; ARMS=('ELIGIBILITY_TRACE','NO_TRACE','BPTT')
NI,NH,NC=4,24,2; LEAK=.1; TRACE_DECAY=.98; LR=.03; CLIP=1.0; NTRAIN=3000; NTEST=500; NOISE=.25
NBOOT=20000; BOOT_SEED=2026101010

def softmax(z):
 e=np.exp(z-np.max(z));return e/e.sum()
def init(seed):
 r=np.random.default_rng(seed);q,_=np.linalg.qr(r.normal(size=(NH,NH)))
 return {'Wx':r.normal(0,.5,(NH,NI)),'Wh':.9*q,'b':np.zeros(NH),'Wo':r.normal(0,.01,(NC,NH)),'bo':np.zeros(NC)}
def episode(rng,delay=DELAY):
 a,b=(int(v) for v in rng.integers(0,2,2));x=np.zeros((delay+3,NI));x[0,a]=1;x[1:delay+1]=rng.normal(0,NOISE,(delay,NI));x[delay+1,2+b]=1
 return x,a^b

def forward(x,w):
 h=np.zeros(NH);hs=[];phis=[];eh=np.zeros((NH,NH));ex=np.zeros((NH,NI));eb=np.zeros(NH)
 for xt in x:
  hp=h;z=np.tanh(w['Wx']@xt+w['Wh']@hp+w['b']);phi=LEAK*(1-z*z);h=(1-LEAK)*hp+LEAK*z
  eh=TRACE_DECAY*eh+np.outer(phi,hp);ex=TRACE_DECAY*ex+np.outer(phi,xt);eb=TRACE_DECAY*eb+phi
  hs.append(h.copy());phis.append(phi.copy())
 return h,np.asarray(hs),np.asarray(phis),eh,ex,eb

def gradients(x,y,w,arm):
 h,hs,phis,eh,ex,eb=forward(x,w);p=softmax(w['Wo']@h+w['bo']);d=p.copy();d[y]-=1
 g={k:np.zeros_like(v) for k,v in w.items()};g['Wo']=np.outer(d,h);g['bo']=d
 if arm=='BPTT':
  dhnext=np.zeros(NH)
  for t in range(len(x)-1,-1,-1):
   hp=hs[t-1] if t else np.zeros(NH);dh=(w['Wo'].T@d if t==len(x)-1 else 0)+dhnext;du=dh*phis[t]
   g['Wx']+=np.outer(du,x[t]);g['Wh']+=np.outer(du,hp);g['b']+=du;dhnext=(1-LEAK)*dh+w['Wh'].T@du
 else:
  if arm=='NO_TRACE':
   hp=hs[-2];eh=np.outer(phis[-1],hp);ex=np.outer(phis[-1],x[-1]);eb=phis[-1].copy()
  signal=w['Wo'].T@d;g['Wh']=signal[:,None]*eh;g['Wx']=signal[:,None]*ex;g['b']=signal*eb
 return g,int(np.argmax(p)),-math.log(max(float(p[y]),1e-300))

def update(w,g,state,t):
 norm=math.sqrt(sum(float(np.sum(v*v)) for v in g.values()));scale=min(1.,CLIP/max(norm,1e-12))
 m,v=state
 for k in w:
  z=g[k]*scale;m[k]=.9*m[k]+.1*z;v[k]=.999*v[k]+.001*z*z
  mh=m[k]/(1-.9**t);vh=v[k]/(1-.999**t);w[k]-=LR*mh/(np.sqrt(vh)+1e-8)
 if not all(np.isfinite(a).all() for a in w.values()):raise FloatingPointError('nonfinite weights')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ci(v):
 r=np.random.default_rng(BOOT_SEED);idx=r.integers(0,len(v),(NBOOT,len(v)));b=v[idx].mean(1);return [float(z) for z in np.quantile(b,[.025,.975])]
def csvwrite(p,rows):
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def preflight():
 w=init(78123);rng=np.random.default_rng(9917);x,y=episode(rng);g,_,_=gradients(x,y,w,'BPTT');eps=1e-6;checks=[]
 for k,idx in [('Wx',(0,0)),('Wx',(3,2)),('Wh',(0,1)),('Wh',(7,9)),('b',(4,)),('Wo',(1,5)),('bo',(0,))]:
  o=w[k][idx];w[k][idx]=o+eps;lp=gradients(x,y,w,'BPTT')[2];w[k][idx]=o-eps;lm=gradients(x,y,w,'BPTT')[2];w[k][idx]=o;checks.append(abs((lp-lm)/(2*eps)-g[k][idx]))
 if max(checks)>2e-6:raise AssertionError(f'gradient check {max(checks)}')
 assert [a^b for a in (0,1) for b in (0,1)]==[0,1,1,0] and len(x)==7
 payload={'experiment_id':'M5_ELIGIBILITY_TEMPORAL_XOR_V2','classification':'POST_RESULT_EXPLORATORY_OPTIMIZATION','python':platform.python_version(),'numpy':np.__version__,'contract_sha256':sha(CONTRACT),'runner_sha256':sha(Path(__file__)),'config':{'seeds':[SEEDS[0],SEEDS[-1]],'delay':DELAY,'arms':ARMS,'train_episodes':NTRAIN,'test_episodes':NTEST,'hidden_units':NH,'optimizer':'Adam','learning_rate':LR,'trace_decay':TRACE_DECAY,'bootstrap_resamples':NBOOT,'bootstrap_seed':BOOT_SEED},'gradient_check_max_abs_error':max(checks),'xor_truth_table':'PASS','timing_check':'PASS','outcomes_computed':False}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'PREFLIGHT.json').write_text(json.dumps(payload,indent=2)+'\n');return payload

def run():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for si,seed in enumerate(SEEDS):
  rng=np.random.default_rng(seed*1000003+DELAY*101+1);train=[episode(rng) for _ in range(NTRAIN)];te=np.random.default_rng(seed*1000003+DELAY*101+2);test=[episode(te) for _ in range(NTEST)]
  w0=init(seed*101+31)
  for arm in ARMS:
   w={k:v.copy() for k,v in w0.items()};state=({k:np.zeros_like(v) for k,v in w.items()},{k:np.zeros_like(v) for k,v in w.items()})
   for t,(x,y) in enumerate(train,1):g,_,_=gradients(x,y,w,arm);update(w,g,state,t)
   correct=0;loss=0.
   for x,y in test:_,pred,l=gradients(x,y,w,'NO_TRACE');correct+=pred==y;loss+=l
   rows.append({'task_seed':seed,'delay':DELAY,'arm':arm,'train_episodes':NTRAIN,'test_episodes':NTEST,'accuracy':correct/NTEST,'cross_entropy':loss/NTEST})
  if si%5==0:print(f'completed seed {seed}',flush=True)
 csvwrite(OUT/'task_seed_results.csv',rows);per=[]
 for seed in SEEDS:
  d={r['arm']:r['accuracy'] for r in rows if r['task_seed']==seed};per.append({'task_seed':seed,**d,'trace_minus_no_trace':d['ELIGIBILITY_TRACE']-d['NO_TRACE'],'trace_minus_bptt':d['ELIGIBILITY_TRACE']-d['BPTT']})
 csvwrite(OUT/'paired_seed_contrasts.csv',per)
 means={a:float(np.mean([r['accuracy'] for r in rows if r['arm']==a])) for a in ARMS};diff=np.array([r['trace_minus_no_trace'] for r in per]);bptt=np.array([r['BPTT'] for r in per]);result={'experiment_id':'M5_ELIGIBILITY_TEMPORAL_XOR_V2','classification':'POST_RESULT_EXPLORATORY_OPTIMIZATION','primary_unit':'task_seed','n_task_seeds':len(SEEDS),'delay':DELAY,'arm_mean_accuracy':means,'primary_trace_minus_no_trace':{'mean':float(diff.mean()),'ci95':ci(diff),'positive_seed_count':int((diff>0).sum())},'trace_minus_bptt':{'mean':float(np.mean([r['trace_minus_bptt'] for r in per])),'ci95':ci(np.array([r['trace_minus_bptt'] for r in per]))},'bptt_viability':{'mean':float(bptt.mean()),'ci95':ci(bptt),'chance':.5,'viable':bool(ci(bptt)[0]>.5)},'optimizer':'Adam(lr=0.03,beta1=0.9,beta2=0.999,eps=1e-8)','train_episodes_per_arm_seed':NTRAIN,'test_episodes_per_seed_arm':NTEST,'bootstrap_resamples':NBOOT,'bootstrap_seed':BOOT_SEED}
 (OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n');files=['task_seed_results.csv','paired_seed_contrasts.csv','summary.json'];manifest={'experiment_id':result['experiment_id'],'python':platform.python_version(),'numpy':np.__version__,'preflight_sha256':sha(OUT/'PREFLIGHT.json'),'contract_sha256':sha(CONTRACT),'runner_sha256':sha(Path(__file__)),'sha256':{f:sha(OUT/f) for f in files}};(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return result
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--preflight',action='store_true');a=ap.parse_args();print(json.dumps(preflight() if a.preflight else run(),indent=2))

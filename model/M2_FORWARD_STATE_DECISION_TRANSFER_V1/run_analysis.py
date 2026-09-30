#!/usr/bin/env python3
"""Evaluate frozen V3 state estimators on three post hoc decision readouts."""
import argparse,csv,json,math,sys
from pathlib import Path
import numpy as np,torch
ROOT=Path(__file__).resolve().parents[2];V3=ROOT/'model/M2_FORWARD_STATE_SENSORY_GATE_V3';sys.path.insert(0,str(V3))
import run_experiment as source
ID='M2_FORWARD_STATE_DECISION_TRANSFER_V1';ENVS=source.ENVIRONMENTS;CONDS=source.CONDITIONS
POLICIES=source.POLICIES;TRAINED=POLICIES[:-1];TASKS=('SIGN_CHOICE','THRESHOLD_CHOICE','PERSISTENT_SIGN_ACTION')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'data/results'/ID);out=ap.parse_args().output_dir.resolve()
 if out.exists() and any(out.iterdir()):raise FileExistsError(out)
 torch.set_num_threads(1);out.mkdir(parents=True,exist_ok=True);stored={}
 with (ROOT/'data/results/M2_FORWARD_STATE_SENSORY_GATE_V3/learned_parameters.csv').open() as f:
  for r in csv.DictReader(f):stored[(int(r['train_seed']),r['policy'])]=json.loads(r['parameters_json'])
 rows=[];param_order={f:i for i,f in enumerate(TRAINED)}
 for env_i,env in enumerate(ENVS):
  base=source.generate(620000+env_i,512,env,'ALIGNED');x0,q0,_,phi,sp,so=base
  for cond in CONDS:
   x,q,y,*_=source.generate(620000+env_i,512,env,cond)
   assert np.array_equal(x,x0) and np.array_equal(q,q0),'test streams diverged across conditions'
   for seed in range(42000,42020):
    preds={}
    for f in TRAINED:
     m=source.Model(f,seed+1009*(param_order[f]+1));vals=stored[(seed,f)]
     with torch.no_grad():
      if f=='GRU_1D':
       for p,a in zip(m.parameters(),vals):p.copy_(torch.tensor(a,dtype=p.dtype))
      else:m.raw.copy_(torch.tensor(vals,dtype=m.raw.dtype))
      preds[f]=m.rollout(torch.from_numpy(y),torch.from_numpy(q.astype(np.float32))).numpy()
    preds['KALMAN_ORACLE']=source.oracle(y,q,phi,sp,so,cond)
    for f,pred in preds.items():
     action=np.where(pred[:,1:]>=0,1,-1);target=np.where(x[:,1:]>=0,1,-1);correct=(action==target)
     sign_accuracy=correct.mean(1)
     engage=pred>=.5;step_reward=np.where(engage,x-.5,0);oracle_reward=np.maximum(x-.5,0);regret=(oracle_reward-step_reward).mean(1);mean_reward=step_reward.mean(1)
     act=np.where(pred[:,1:]>=0,1,-1);switch=np.zeros_like(act,dtype=bool);switch[:,1:]=act[:,1:]!=act[:,:-1];persistent=(correct.astype(float)-.10*switch).mean(1)
     for ep in range(512):rows.append({'train_seed':seed,'environment':env,'condition':cond,'episode_id':ep,'policy':f,'sign_choice_accuracy':float(sign_accuracy[ep]),'threshold_mean_reward':float(mean_reward[ep]),'threshold_regret':float(regret[ep]),'persistent_action_utility':float(persistent[ep])})
   print(f'evaluated {env}/{cond}',flush=True)
 with (out/'episode_decisions.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 summary={}
 for env in ENVS:
  summary[env]={}
  for cond in CONDS:
   summary[env][cond]={}
   for task,metric in [('SIGN_CHOICE','sign_choice_accuracy'),('THRESHOLD_CHOICE','threshold_mean_reward'),('THRESHOLD_REGRET','threshold_regret'),('PERSISTENT_SIGN_ACTION','persistent_action_utility')]:
    summary[env][cond][task]={p:float(np.mean([r[metric] for r in rows if r['environment']==env and r['condition']==cond and r['policy']==p])) for p in POLICIES}
 (out/'summary.json').write_text(json.dumps({'analysis_id':ID,'source_experiment':'M2_FORWARD_STATE_SENSORY_GATE_V3','summary':summary},indent=2)+'\n')
 print(json.dumps(summary['IN_RANGE'],indent=2))
if __name__=='__main__':main()

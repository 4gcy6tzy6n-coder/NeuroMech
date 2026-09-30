#!/usr/bin/env python3
"""Unit-safe paired analysis of M7 raw outcomes; classification and regression stay separate."""
import csv,json
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'results'/'M7_TEMPORAL_CORRELATION_BOUNDARY'/'task_metrics.csv'
OUT=ROOT/'data'/'results'/'M7_TEMPORAL_CORRELATION_BOUNDARY'/'analysis_v1_objective_stratified.json'
RHOS=(0.0,0.2,0.4,0.6,0.8,0.9); DELAYS=(1,4,16,64); OBJECTIVES=('CLASSIFICATION','REGRESSION'); SEEDS=30; BOOT=20000
rows=list(csv.DictReader(DATA.open()))
score={}
for r in rows:
 key=(r['objective'],float(r['rho']),int(r['seed']),int(r['delay']),r['arm'])
 assert key not in score
 score[key]=float(r['score'])
assert len(score)==4320
benefit={}
replay_diff={}
for o in OBJECTIVES:
 for rho in RHOS:
  for d in DELAYS:
   vals=[]; replay=[]
   for s in range(SEEDS):
    tr=score[(o,rho,s,d,'ELIGIBILITY_TRACE')]
    no=score[(o,rho,s,d,'NO_TRACE')]
    rp=score[(o,rho,s,d,'EXACT_REPLAY')]
    vals.append(tr-no if o=='CLASSIFICATION' else no-tr)
    replay.append(tr-rp if o=='CLASSIFICATION' else rp-tr)
   benefit[(o,rho,d)]=np.array(vals)
   replay_diff[(o,rho,d)]=np.array(replay)

def ci(v,seed):
 rng=np.random.default_rng(seed); v=np.asarray(v); ids=rng.integers(0,len(v),(BOOT,len(v)))
 m=v[ids].mean(1)
 return [float(np.quantile(m,.025)),float(np.quantile(m,.975))]
cell=[]
for oi,o in enumerate(OBJECTIVES):
 for ri,rho in enumerate(RHOS):
  for d in DELAYS:
   v=benefit[(o,rho,d)]
   rv=replay_diff[(o,rho,d)]
   cell.append({'objective':o,'rho':rho,'delay':d,'trace_benefit_mean':float(v.mean()),'trace_benefit_seed_bootstrap_95ci':ci(v,50000+oi*10000+ri*100+d),'trace_minus_replay_oracle_mean':float(rv.mean())})
interactions={}
for oi,o in enumerate(OBJECTIVES):
 per_seed_by_delay={}
 for d in DELAYS:
  per_seed_by_delay[d]=benefit[(o,0.0,d)]-benefit[(o,0.9,d)]
  v=per_seed_by_delay[d]
  interactions.setdefault(o,{})[str(d)]={'rho0_minus_rho09':float(v.mean()),'seed_bootstrap_95ci':ci(v,70000+oi*1000+d)}
 mean_seed=np.mean(np.stack(list(per_seed_by_delay.values())),axis=0)
 interactions[o]['equal_delay_mean']={'rho0_minus_rho09':float(mean_seed.mean()),'seed_bootstrap_95ci':ci(mean_seed,80000+oi),'positive_seed_count':int((mean_seed>0).sum())}
result={'status':'OBJECTIVE_STRATIFIED_REANALYSIS; ORIGINAL_POOLED_INTERACTION_INVALID_MIXED_UNITS',
 'why_pooled_invalid':'The initial run summary averaged accuracy-point differences with MSE-point differences; their scales are not commensurate. No pooled cross-objective estimate is reported.',
 'n_rows':len(rows),'cells':cell,'interactions_by_objective_and_delay':interactions,
 'interpretation_note':'Positive benefit means trace helps (accuracy gain or MSE reduction). Positive rho0-minus-rho09 means the trace benefit is greater for IID than highly autocorrelated input. Objective-specific estimates are not combined.'}
OUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'rows':len(rows),'interactions':interactions},indent=2))

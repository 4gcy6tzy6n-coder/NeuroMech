#!/usr/bin/env python3
"""Recompute summaries and checksums for the frozen-model decision probe."""
import csv,hashlib,json,platform
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];ID='M2_FORWARD_STATE_DECISION_TRANSFER_V1';ENVS=('IN_RANGE','HIGH_PERSISTENCE','LOW_PERSISTENCE');CONDS=('ALIGNED','INDEPENDENT','REVERSED')
METRICS=('sign_choice_accuracy','threshold_mean_reward','threshold_regret','persistent_action_utility');POLICIES=('MODE_GAIN_FILTER','CONSTANT_GAIN_FILTER','GENERIC_RNN_1D','BILINEAR_RNN_1D','GRU_1D','KALMAN_ORACLE')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'data/results'/ID;rows=list(csv.DictReader((out/'episode_decisions.csv').open()));s={}
 for env in ENVS:
  s[env]={}
  for cond in CONDS:
   s[env][cond]={}
   for metric in METRICS:s[env][cond][metric]={p:float(np.mean([float(r[metric]) for r in rows if r['environment']==env and r['condition']==cond and r['policy']==p])) for p in POLICIES}
 (out/'summary.json').write_text(json.dumps({'analysis_id':ID,'source_experiment':'M2_FORWARD_STATE_SENSORY_GATE_V3','summary':s},indent=2)+'\n')
 names=('episode_decisions.csv','summary.json');man={'analysis_id':ID,'source_experiment':'M2_FORWARD_STATE_SENSORY_GATE_V3','source_v3_commit':'1562202b280c7096051fdb76eb6db30401b7b2c0','python':platform.python_version(),'numpy':np.__version__,'n_training_seeds':20,'test_episodes_per_environment':512,'horizon':160,'metrics':list(METRICS),'sha256':{n:sha(out/n) for n in names}}
 (out/'manifest.json').write_text(json.dumps(man,indent=2)+'\n');print(json.dumps(s['IN_RANGE'],indent=2))
if __name__=='__main__':main()

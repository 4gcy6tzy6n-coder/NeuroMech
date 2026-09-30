#!/usr/bin/env python3
"""Independent row-integrity and summary verification of decision utility outputs."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];ENVS=('IN_RANGE','HIGH_PERSISTENCE','LOW_PERSISTENCE');CONDS=('ALIGNED','INDEPENDENT','REVERSED');POLICIES=('MODE_GAIN_FILTER','CONSTANT_GAIN_FILTER','GENERIC_RNN_1D','BILINEAR_RNN_1D','GRU_1D','KALMAN_ORACLE');METRICS=('sign_choice_accuracy','threshold_mean_reward','threshold_regret','persistent_action_utility')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_FORWARD_STATE_DECISION_TRANSFER_V1');d=ap.parse_args().results_dir;m=json.loads((d/'manifest.json').read_text());assert m['analysis_id']=='M2_FORWARD_STATE_DECISION_TRANSFER_V1'
 for n,h in m['sha256'].items():assert sha(d/n)==h,(n,'checksum mismatch')
 rows=list(csv.DictReader((d/'episode_decisions.csv').open()));expected=20*3*3*512*6;assert len(rows)==expected,len(rows);keys={(r['train_seed'],r['environment'],r['condition'],r['episode_id'],r['policy']) for r in rows};assert len(keys)==expected
 s=json.loads((d/'summary.json').read_text())['summary'];totals={};counts={}
 for r in rows:
  k=(r['environment'],r['condition'],r['policy'])
  if k not in totals:totals[k]={m:0.0 for m in METRICS};counts[k]=0
  counts[k]+=1
  for metric in METRICS:totals[k][metric]+=float(r[metric])
 nchecks=0
 for env in ENVS:
  for cond in CONDS:
   for metric in METRICS:
    for p in POLICIES:
     v=totals[(env,cond,p)][metric]/counts[(env,cond,p)];assert abs(v-s[env][cond][metric][p])<1e-12,(env,cond,metric,p);nchecks+=1
 print(json.dumps({'status':'PASS','rows':len(rows),'unique_rows':len(keys),'means_recomputed':nchecks,'checksums':'PASS'},indent=2))
if __name__=='__main__':main()

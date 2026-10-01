#!/usr/bin/env python3
"""Independent row, contrast, yoke, and hash checks for M2 discrete-state V1."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];NAME='M2_DISCRETE_MOTOR_STATE_TRANSFER_V1'
PROFILES=('TRAIN_LIKE','LONG_BURST','LOW_MISSING','FAST_TARGET')
ARMS=('SELF_STATE','ZERO_STATE','ACTION_STATE','YOKED_STATE','REACTIVE')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results'/NAME/'canonical');out=ap.parse_args().results_dir
 fits=rows(out/'fit_manifest.csv');eps=rows(out/'episode_metrics.csv');summ=rows(out/'seed_summary.csv');summary=json.loads((out/'summary.json').read_text());man=json.loads((out/'manifest.json').read_text());yokes=json.loads((out/'yoke_checks.json').read_text())
 assert len(fits)==32*4 and len(eps)==32*4*5*128 and len(summ)==32*4*5
 assert {r['arm'] for r in fits}==set(ARMS[:-1]) and {r['arm'] for r in eps}==set(ARMS)
 assert {r['profile'] for r in eps}==set(PROFILES)
 assert all(int(r['parameter_count'])==321 and int(r['updates'])==160 for r in fits)
 groups={};seen=set()
 for r in eps:
  key=(int(r['seed_block']),r['profile'],r['arm'],int(r['episode_id']));assert key not in seen;seen.add(key);groups.setdefault(key[:3],[]).append(r)
  for m in ('tracking_mse','command_energy','missing_fraction'):assert np.isfinite(float(r[m]))
 assert all(len(v)==128 for v in groups.values())
 recomputed={k:{m:float(np.mean([float(r[m]) for r in v])) for m in ('tracking_mse','command_energy','missing_fraction')} for k,v in groups.items()}
 for r in summ:
  k=(int(r['seed_block']),r['profile'],r['arm']);assert int(r['n_episodes'])==128
  for m in recomputed[k]:assert np.isclose(float(r[m]),recomputed[k][m],rtol=1e-11,atol=1e-12)
 def blockmean(b,a):return recomputed[(b,'LONG_BURST',a)]['tracking_mse']
 others={'self_minus_action':'ACTION_STATE','self_minus_zero':'ZERO_STATE','self_minus_yoke':'YOKED_STATE','self_minus_reactive':'REACTIVE'}
 for key,other in others.items():
  vals=[blockmean(b,'SELF_STATE')-blockmean(b,other) for b in range(32)];record=summary['contrasts'][key]
  assert np.allclose(vals,record['seed_block_values'],rtol=1e-11,atol=1e-12)
  assert np.isclose(np.mean(vals),record['summary']['mean'],rtol=1e-11,atol=1e-12)
 assert len(yokes)==32*len(PROFILES) and all(x['no_fixed_points'] and x['exact_per_time_distribution_match'] for x in yokes)
 for f,d in man['outputs'].items():assert (out/f).stat().st_size==d['bytes'] and sha(out/f)==d['sha256']
 for p,key in ((ROOT/'summery'/NAME/'CONTRACT.md','contract_sha256'),(ROOT/'model'/NAME/'run_experiment.py','runner_sha256'),(ROOT/'model'/NAME/'verify_results.py','verifier_sha256')):assert sha(p)==man[key]
 print(json.dumps({'status':'PASS','fit_rows':len(fits),'episode_rows':len(eps),'summary_rows':len(summ),'yoke_checks':len(yokes),'checks':['row completeness','episode uniqueness','parameter/update matching','metric validity','seed summary recomputation','paired primary/secondary contrast recomputation','exact per-time yoke distribution','manifest and source hashes']},indent=2))
if __name__=='__main__':main()

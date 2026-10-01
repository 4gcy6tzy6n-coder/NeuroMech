#!/usr/bin/env python3
"""Independent structural and arithmetic verifier for actuation-dose run."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];NAME='M2_ACTUATION_UNCERTAINTY_STATE_FEEDBACK_V1'
LEVELS=('0.0','0.1','0.25','0.4');ARMS=('SELF_STATE','ACTION_STATE','ZERO_STATE','YOKED_STATE','REACTIVE')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def verify(out):
 fits=read(out/'fit_manifest.csv');eps=read(out/'episode_metrics.csv');ss=read(out/'seed_summary.csv');sm=json.loads((out/'summary.json').read_text());man=json.loads((out/'manifest.json').read_text());y=json.loads((out/'yoke_checks.json').read_text())
 n=len(man['training_seeds']);nt=128
 assert len(fits)==n*4 and len(eps)==n*4*5*nt and len(ss)==n*4*5
 assert {r['arm'] for r in fits}==set(ARMS[:-1]) and {r['arm'] for r in eps}==set(ARMS)
 assert {r['reverse_probability'] for r in eps}==set(LEVELS)
 assert all(int(r['parameter_count'])==321 and int(r['updates'])==160 for r in fits)
 groups={};seen=set()
 for r in eps:
  k=(int(r['seed_block']),r['reverse_probability'],r['arm'],int(r['episode_id']));assert k not in seen;seen.add(k);groups.setdefault(k[:3],[]).append(r)
  for q in ('tracking_mse','command_energy','missing_fraction'):assert np.isfinite(float(r[q]))
 assert all(len(v)==nt for v in groups.values())
 means={k:{q:float(np.mean([float(r[q]) for r in v])) for q in ('tracking_mse','command_energy','missing_fraction')} for k,v in groups.items()}
 for r in ss:
  k=(int(r['seed_block']),r['reverse_probability'],r['arm']);assert int(r['n_episodes'])==nt
  for q in means[k]:assert np.isclose(float(r[q]),means[k][q],rtol=1e-11,atol=1e-12)
 def m(b,a,p):return means[(b,str(p),a)]['tracking_mse']
 adv={str(p):[m(b,'ACTION_STATE',p)-m(b,'SELF_STATE',p) for b in range(n)] for p in (0.0,.1,.25,.4)}
 for p,v in adv.items():assert np.allclose(v,sm['advantage_by_reverse_probability'][p]['seed_block_values'],rtol=1e-11,atol=1e-12)
 inter=[adv['0.4'][b]-adv['0.0'][b] for b in range(n)]
 assert np.allclose(inter,sm['primary_interaction_seed_block_values'],rtol=1e-11,atol=1e-12)
 assert len(y)==n*4 and all(a['no_fixed_points'] and a['exact_per_time_distribution_match'] for a in y)
 for f,d in man['outputs'].items():assert (out/f).stat().st_size==d['bytes'] and sha(out/f)==d['sha256']
 for p,k in ((ROOT/'summery'/NAME/'CONTRACT.md','contract_sha256'),(ROOT/'model'/NAME/'run_experiment.py','runner_sha256'),(ROOT/'model'/NAME/'verify_results.py','verifier_sha256')):assert sha(p)==man[k]
 return {'status':'PASS','fit_rows':len(fits),'episode_rows':len(eps),'seed_summary_rows':len(ss),'yoke_checks':len(y),'checks':['row completeness/uniqueness','parameter and update accounting','finite episode metrics','seed-summary recomputation','dose contrasts and interaction recomputation','exact yoke distribution checks','output and source hashes']}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results'/NAME/'canonical');a=ap.parse_args();print(json.dumps(verify(a.results_dir),indent=2))
if __name__=='__main__':main()

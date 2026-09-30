#!/usr/bin/env python3
"""Independently recompute the V2 seed-level result and verify all hashes."""
import csv, hashlib, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'data/results/M5_ELIGIBILITY_TEMPORAL_XOR_V2'
CONTRACT=ROOT/'summery/M5_ELIGIBILITY_TEMPORAL_XOR_V2/CONTRACT.md'; RUNNER=Path(__file__).resolve().with_name('run_experiment.py')
SEEDS=range(1000,1030); ARMS=('ELIGIBILITY_TRACE','NO_TRACE','BPTT'); NBOOT=20000; BOOT_SEED=2026101010
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ci(x):
 r=np.random.default_rng(BOOT_SEED);b=x[r.integers(0,len(x),(NBOOT,len(x)))].mean(1);return [float(z) for z in np.quantile(b,[.025,.975])]
def main():
 manifest=json.loads((OUT/'manifest.json').read_text()); pre=json.loads((OUT/'PREFLIGHT.json').read_text())
 assert manifest['contract_sha256']==sha(CONTRACT) and manifest['runner_sha256']==sha(RUNNER)
 assert manifest['preflight_sha256']==sha(OUT/'PREFLIGHT.json') and pre['outcomes_computed'] is False
 rows=list(csv.DictReader((OUT/'task_seed_results.csv').open())); assert len(rows)==90
 table={}
 for r in rows:
  k=(int(r['task_seed']),r['arm']);assert k not in table and k[0] in SEEDS and k[1] in ARMS
  a=float(r['accuracy']);l=float(r['cross_entropy']);assert np.isfinite(a) and 0<=a<=1 and np.isfinite(l) and l>=0
  assert int(r['train_episodes'])==3000 and int(r['test_episodes'])==500;table[k]=a
 assert len(table)==90
 contrasts=np.array([table[(s,'ELIGIBILITY_TRACE')]-table[(s,'NO_TRACE')] for s in SEEDS]);bptt=np.array([table[(s,'BPTT')] for s in SEEDS])
 summary=json.loads((OUT/'summary.json').read_text());p=summary['primary_trace_minus_no_trace'];v=summary['bptt_viability']
 assert abs(float(contrasts.mean())-p['mean'])<1e-12 and np.allclose(ci(contrasts),p['ci95'],atol=1e-12)
 assert int((contrasts>0).sum())==p['positive_seed_count'];assert abs(float(bptt.mean())-v['mean'])<1e-12 and np.allclose(ci(bptt),v['ci95'],atol=1e-12)
 assert bool(ci(bptt)[0]>.5)==bool(v['viable'])
 for name,digest in manifest['sha256'].items():assert sha(OUT/name)==digest,(name,'checksum mismatch')
 report={'status':'PASS','rows':len(rows),'unique_seed_arm_cells':len(table),'seed_contrasts_recomputed':True,'bootstrap_intervals_recomputed':True,'checksums':'PASS','primary_mean':float(contrasts.mean()),'primary_ci95':ci(contrasts),'bptt_viability':bool(ci(bptt)[0]>.5)}
 (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');manifest['verification_sha256']=sha(OUT/'verification.json');manifest['verifier_sha256']=sha(Path(__file__));manifest['verification_status']='PASS';(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

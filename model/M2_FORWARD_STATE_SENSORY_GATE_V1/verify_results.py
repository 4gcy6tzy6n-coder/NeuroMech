#!/usr/bin/env python3
"""Independent integrity and estimand check for archived M2 gate results."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_FORWARD_STATE_SENSORY_GATE_V1'); d=ap.parse_args().results_dir
 man=json.loads((d/'manifest.json').read_text()); assert man['experiment_id']=='M2_FORWARD_STATE_SENSORY_GATE_V1'
 for name,digest in man['sha256'].items(): assert sha(d/name)==digest,(name,'checksum mismatch')
 rows=list(csv.DictReader((d/'episode_metrics.csv').open())); assert len(rows)==20*3*512*5, len(rows)
 assert len({(r['train_seed'],r['condition'],r['episode_id'],r['policy']) for r in rows})==len(rows)
 s=json.loads((d/'summary.json').read_text())['summary']; diffs=[]
 for r in rows:
  if r['condition']=='ALIGNED' and r['policy'] in ('MODE_GAIN_FILTER','GENERIC_RNN_1D'):
   diffs.append((int(r['train_seed']),int(r['episode_id']),r['policy'],float(r['episode_mse'])))
 from collections import defaultdict
 z=defaultdict(dict)
 for seed,ep,p,mse in diffs:z[(seed,ep)][p]=mse
 contrast=np.array([v['GENERIC_RNN_1D']-v['MODE_GAIN_FILTER'] for v in z.values()]); observed=contrast.mean(); recorded=s['ALIGNED']['primary_contrast']['generic_minus_mode_mse']
 assert abs(observed-recorded)<1e-10,(observed,recorded)
 assert len(z)==20*512
 print(json.dumps({'status':'PASS','metric_rows':len(rows),'primary_contrast_recomputed':float(observed),'recorded':recorded,'checksums':'PASS'},indent=2))
if __name__=='__main__':main()

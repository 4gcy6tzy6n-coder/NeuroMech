#!/usr/bin/env python3
"""Independent row and primary crossed-bootstrap verification."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results/M2_CLOSED_LOOP_ACTIVE_SENSING_V1');d=ap.parse_args().results_dir;m=json.loads((d/'manifest.json').read_text());assert m['experiment_id']=='M2_CLOSED_LOOP_ACTIVE_SENSING_V1'
 for n,h in m['sha256'].items():assert sha(d/n)==h,(n,'hash mismatch')
 rows=list(csv.DictReader((d/'episode_control.csv').open()));keys={(r['train_seed'],r['condition'],r['episode_id'],r['policy']) for r in rows};assert len(rows)==20*3*512*6 and len(keys)==len(rows)
 grouped={p:np.empty((20,512)) for p in ('MODE_GAIN_FILTER','CONSTANT_GAIN_FILTER')}
 for r in rows:
  if r['condition']=='ALIGNED' and r['policy'] in grouped:grouped[r['policy']][int(r['train_seed'])-42000,int(r['episode_id'])]=float(r['mean_distance'])
 diff=grouped['CONSTANT_GAIN_FILTER']-grouped['MODE_GAIN_FILTER'];s=json.loads((d/'summary.json').read_text())['summary']['ALIGNED']['contrasts']['CONSTANT_GAIN_FILTER_minus_mode_mean_distance'];assert abs(float(diff.mean())-s['mean_difference'])<1e-12
 rng=np.random.default_rng(20261008);bs=np.empty(20000)
 for start in range(0,len(bs),128):
  n=min(128,len(bs)-start);si=rng.integers(0,20,(n,20));ei=rng.integers(0,512,(n,512));bs[start:start+n]=diff[si[:,:,None],ei[:,None,:]].mean((1,2))
 assert np.allclose(np.quantile(bs,[.025,.975]),s['crossed_95_percent_bootstrap_interval'],atol=1e-10)
 print(json.dumps({'status':'PASS','rows':len(rows),'unique_rows':len(keys),'primary_mean_difference':float(diff.mean()),'primary_interval':s['crossed_95_percent_bootstrap_interval'],'checksums':'PASS'},indent=2))
if __name__=='__main__':main()

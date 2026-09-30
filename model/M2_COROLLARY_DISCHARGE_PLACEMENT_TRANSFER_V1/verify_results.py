#!/usr/bin/env python3
"""Independent integrity and primary-statistic verifier."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];EXP='M2_COROLLARY_DISCHARGE_PLACEMENT_TRANSFER_V1'
SEEDS=np.arange(88000,88030);HAZARDS=(.01,.05,.20);ARMS=('SENSORY_SITE_CD','OUTPUT_SITE_PERSISTENCE','NO_FEEDBACK','GENERIC_RNN_2H','BAYES_FILTER')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ci(x,seed):
    rng=np.random.default_rng(seed);b=np.empty(10000)
    for start in range(0,10000,128):
        n=min(128,10000-start);s=rng.integers(0,30,(n,30));e=rng.integers(0,512,(n,512));b[start:start+n]=x[s[:,:,None],e[:,None,:]].mean((1,2))
    return np.quantile(b,[.025,.975])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results'/EXP/'canonical');d=ap.parse_args().results_dir.resolve();m=json.loads((d/'run_manifest.json').read_text());assert m['experiment_id']==EXP
    for f,digest in m['files'].items():assert sha(d/f)==digest,(f,'checksum')
    src=m['analysis_sources']
    for k,f in [('runner','run_experiment.py'),('analyzer','analyze_results.py'),('verifier','verify_results.py')]:assert sha(ROOT/'model'/EXP/f)==src[k],(k,'source hash')
    assert sha(ROOT/'summery'/EXP/'CONTRACT.md')==src['contract']
    si={int(v):i for i,v in enumerate(SEEDS)};hi={v:i for i,v in enumerate(HAZARDS)};ai={v:i for i,v in enumerate(ARMS)};a=np.full((30,3,512,5,3),np.nan);seen=set()
    with (d/'episode_metrics.csv').open() as f:
        for row in csv.DictReader(f):
            key=(int(row['training_seed']),float(row['hazard']),int(row['episode_id']),row['arm']);assert key not in seen;seen.add(key)
            ix=(si[key[0]],hi[key[1]],key[2],ai[key[3]])
            a[ix+(0,)]=float(row['accuracy']);a[ix+(1,)]=float(row['false_action_switch_rate'])
            if row['switch_recovery_lag']:a[ix+(2,)]=float(row['switch_recovery_lag'])
    assert len(seen)==30*3*512*5 and np.isfinite(a[:,:,:,:,:2]).all();assert ((a[:,:,:,:,0]>=0)&(a[:,:,:,:,0]<=1)).all();assert ((a[:,:,:,:,1]>=0)&(a[:,:,:,:,1]<=1)).all()
    s=json.loads((d/'summary.json').read_text());assert s['rows']==len(seen);h=1;delta=a[:,h,:,ai['SENSORY_SITE_CD'],0]-a[:,h,:,ai['OUTPUT_SITE_PERSISTENCE'],0];p=s['primary_contrast']
    assert abs(delta.mean()-p['mean_sensory_minus_output_accuracy'])<1e-12 and np.allclose(ci(delta,20261022),p['crossed_95ci'],atol=1e-12)
    assert int((delta.mean(axis=1)>0).sum())==p['positive_training_seed_count']
    for hi0,hazard in enumerate(HAZARDS):
        for ai0,arm in enumerate(ARMS):
            assert abs(a[:,hi0,:,ai0,0].mean()-s['means'][str(hazard)][arm]['accuracy'])<1e-12
            assert abs(a[:,hi0,:,ai0,1].mean()-s['means'][str(hazard)][arm]['false_action_switch_rate'])<1e-12
    print(json.dumps({'status':'PASS','unique_episode_policy_hazard_keys':len(seen),'primary_interval_recomputed':True,'all_output_and_source_hashes':'PASS'},indent=2))
if __name__=='__main__':main()

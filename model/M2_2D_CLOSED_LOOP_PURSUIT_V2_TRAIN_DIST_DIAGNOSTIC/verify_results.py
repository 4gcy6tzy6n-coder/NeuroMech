#!/usr/bin/env python3
"""Independent row, provenance, and crossed-bootstrap verification for V2."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];EXP='M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC'
SEEDS=np.arange(76000,76030);REGIMES=('RANDOM_ACTION','TEACHER_MIXED_CLOSED_LOOP');CONDS=('ALIGNED','REVERSED')
ARMS=('MODE_GAIN','NO_CONTEXT','ADDITIVE_RNN_MATCHED','BILINEAR_RNN_MATCHED','KALMAN_ORACLE');METRICS=('final_distance','success','mean_distance','steps_to_success')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ci(x,seed):
    rng=np.random.default_rng(seed);b=np.empty(10000)
    for start in range(0,10000,128):
        n=min(128,10000-start);s=rng.integers(0,30,(n,30));e=rng.integers(0,256,(n,256));b[start:start+n]=x[s[:,:,None],e[:,None,:]].mean((1,2))
    return np.quantile(b,[.025,.975])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results'/EXP/'canonical');d=ap.parse_args().results_dir.resolve();m=json.loads((d/'run_manifest.json').read_text());assert m['experiment_id']==EXP
    for f,digest in m['files'].items():assert sha(d/f)==digest,(f,'checksum')
    src=m['analysis_sources']
    for k,f in [('runner','run_experiment.py'),('analyzer','analyze_results.py'),('verifier','verify_results.py')]:assert sha(ROOT/'model'/EXP/f)==src[k],(k,'source hash')
    assert sha(ROOT/'summery'/EXP/'CONTRACT.md')==src['contract']
    si={int(x):i for i,x in enumerate(SEEDS)};ri={x:i for i,x in enumerate(REGIMES)};ci0={x:i for i,x in enumerate(CONDS)};ai={x:i for i,x in enumerate(ARMS)};mi={x:i for i,x in enumerate(METRICS)}
    a=np.full((30,2,2,256,5,4),np.nan);seen=set()
    with (d/'episode_metrics.csv').open() as f:
        for row in csv.DictReader(f):
            k=(int(row['training_seed']),row['regime'],row['condition'],int(row['episode_id']),row['arm']);assert k not in seen;seen.add(k)
            for metric in METRICS:a[si[k[0]],ri[k[1]],ci0[k[2]],k[3],ai[k[4]],mi[metric]]=float(row[metric])
    assert len(seen)==30*2*2*256*5 and np.isfinite(a).all();assert (a[...,mi['final_distance']]>=0).all();assert set(np.unique(a[...,mi['success']])).issubset({0.,1.})
    s=json.loads((d/'summary.json').read_text());assert s['rows']==len(seen)
    # Recompute all reported contrasts and intervals without calling the analyzer.
    check_count=0
    for r in range(2):
      for c in range(2):
       for j,(left,right,name) in enumerate((('BILINEAR_RNN_MATCHED','MODE_GAIN','bilinear_minus_mode'),('ADDITIVE_RNN_MATCHED','MODE_GAIN','additive_minus_mode'),('NO_CONTEXT','MODE_GAIN','no_context_minus_mode'))):
        for metric in ('final_distance','success'):
         delta=a[:,r,c,:,ai[left],mi[metric]]-a[:,r,c,:,ai[right],mi[metric]];rec=s['regime_contrasts'][REGIMES[r]][CONDS[c]][name][metric]
         seed=20261021+r*100+c*20+mi[metric]+j*3
         assert abs(delta.mean()-rec['mean_left_minus_right'])<1e-12
         assert np.allclose(ci(delta,seed),rec['crossed_95ci'],atol=1e-12);check_count+=1
    g=a[:,:,0,:,ai['BILINEAR_RNN_MATCHED'],mi['final_distance']]-a[:,:,0,:,ai['MODE_GAIN'],mi['final_distance']];interaction=g[:,1]-g[:,0];p=s['primary_interaction']
    assert abs(g[:,0].mean()-p['G_random_action']['mean'])<1e-12 and np.allclose(ci(g[:,0],20261021),p['G_random_action']['crossed_95ci'],atol=1e-12)
    assert abs(g[:,1].mean()-p['G_teacher_mixed_closed_loop']['mean'])<1e-12 and np.allclose(ci(g[:,1],20261022),p['G_teacher_mixed_closed_loop']['crossed_95ci'],atol=1e-12)
    assert abs(interaction.mean()-p['interaction_mean'])<1e-12 and np.allclose(ci(interaction,20261023),p['interaction_crossed_95ci'],atol=1e-12)
    assert int((interaction.mean(axis=1)>0).sum())==p['positive_training_seed_count']
    print(json.dumps({'status':'PASS','unique_episode_policy_regime_keys':len(seen),'contrasts_recomputed':check_count+3,'checksums_and_source_hashes':'PASS'},indent=2))
if __name__=='__main__':main()

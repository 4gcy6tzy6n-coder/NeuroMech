#!/usr/bin/env python3
"""Paired analysis for the V2 training-distribution diagnostic."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];EXP='M2_2D_CLOSED_LOOP_PURSUIT_V2_TRAIN_DIST_DIAGNOSTIC'
SEEDS=np.arange(76000,76030);REGIMES=('RANDOM_ACTION','TEACHER_MIXED_CLOSED_LOOP');CONDS=('ALIGNED','REVERSED')
ARMS=('MODE_GAIN','NO_CONTEXT','ADDITIVE_RNN_MATCHED','BILINEAR_RNN_MATCHED','KALMAN_ORACLE');METRICS=('final_distance','success','mean_distance','steps_to_success')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def crossed_ci(x,seed):
    rng=np.random.default_rng(seed);boot=np.empty(10000)
    for start in range(0,10000,128):
        n=min(128,10000-start);si=rng.integers(0,30,(n,30));ei=rng.integers(0,256,(n,256));boot[start:start+n]=x[si[:,:,None],ei[:,None,:]].mean((1,2))
    return np.quantile(boot,[.025,.975]).tolist()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results-dir',type=Path,default=ROOT/'data/results'/EXP/'canonical');d=ap.parse_args().results_dir.resolve();man=json.loads((d/'run_manifest.json').read_text());assert man['experiment_id']==EXP and sha(d/'episode_metrics.csv')==man['files']['episode_metrics.csv']
    si={int(v):i for i,v in enumerate(SEEDS)};ri={v:i for i,v in enumerate(REGIMES)};ci={v:i for i,v in enumerate(CONDS)};ai={v:i for i,v in enumerate(ARMS)};mi={v:i for i,v in enumerate(METRICS)}
    arr=np.full((30,2,2,256,5,4),np.nan,np.float64);keys=set()
    with (d/'episode_metrics.csv').open() as f:
        for r in csv.DictReader(f):
            k=(int(r['training_seed']),r['regime'],r['condition'],int(r['episode_id']),r['arm']);assert k not in keys;keys.add(k)
            for m in METRICS:arr[si[k[0]],ri[k[1]],ci[k[2]],k[3],ai[k[4]],mi[m]]=float(r[m])
    assert len(keys)==30*2*2*256*5 and np.isfinite(arr).all()
    summary={'experiment_id':EXP,'classification':man['classification'],'primary':'ALIGNED interaction: (bilinear-mode final distance)_TEACHER_MIXED_CLOSED_LOOP - (bilinear-mode final distance)_RANDOM_ACTION; positive favors MODE_GAIN under deployment-like training','bootstrap':'paired crossed resampling of training seeds and held-out target IDs','bootstrap_replicates':10000,'rows':len(keys),'mean_metrics':{},'regime_contrasts':{},'primary_interaction':{}}
    for r,regime in enumerate(REGIMES):
        summary['mean_metrics'][regime]={}
        for c,condition in enumerate(CONDS):
            summary['mean_metrics'][regime][condition]={arm:{metric:float(arr[:,r,c,:,a,m].mean()) for m,metric in enumerate(METRICS)} for a,arm in enumerate(ARMS)}
            summary['regime_contrasts'].setdefault(regime,{})[condition]={}
            for name,left,right in (('bilinear_minus_mode','BILINEAR_RNN_MATCHED','MODE_GAIN'),('additive_minus_mode','ADDITIVE_RNN_MATCHED','MODE_GAIN'),('no_context_minus_mode','NO_CONTEXT','MODE_GAIN')):
                for metric in ('final_distance','success'):
                    x=arr[:,r,c,:,ai[left],mi[metric]]-arr[:,r,c,:,ai[right],mi[metric]];summary['regime_contrasts'][regime][condition].setdefault(name,{})[metric]={'mean_left_minus_right':float(x.mean()),'crossed_95ci':[float(v) for v in crossed_ci(x,20261021+r*100+c*20+mi[metric]+('bilinear_minus_mode','additive_minus_mode','no_context_minus_mode').index(name)*3)]}
    g=arr[:,:,0,:,ai['BILINEAR_RNN_MATCHED'],mi['final_distance']]-arr[:,:,0,:,ai['MODE_GAIN'],mi['final_distance']]
    interaction=g[:,1]-g[:,0]
    summary['primary_interaction']={'contrast_name':'G_teacher_mixed - G_random; G = bilinear final distance - mode-gain final distance','G_random_action':{'mean':float(g[:,0].mean()),'crossed_95ci':[float(v) for v in crossed_ci(g[:,0],20261021)]},'G_teacher_mixed_closed_loop':{'mean':float(g[:,1].mean()),'crossed_95ci':[float(v) for v in crossed_ci(g[:,1],20261022)]},'interaction_mean':float(interaction.mean()),'interaction_crossed_95ci':[float(v) for v in crossed_ci(interaction,20261023)],'positive_training_seed_count':int((interaction.mean(axis=1)>0).sum())}
    (d/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    man['files']['summary.json']=sha(d/'summary.json');man['analysis_sources']={'runner':sha(ROOT/'model'/EXP/'run_experiment.py'),'analyzer':sha(Path(__file__)),'verifier':sha(ROOT/'model'/EXP/'verify_results.py'),'contract':sha(ROOT/'summery'/EXP/'CONTRACT.md')};(d/'run_manifest.json').write_text(json.dumps(man,indent=2)+'\n')
    print(json.dumps({'primary_interaction':summary['primary_interaction'],'aligned_metrics':{r:summary['mean_metrics'][r]['ALIGNED'] for r in REGIMES}},indent=2))
if __name__=='__main__':main()

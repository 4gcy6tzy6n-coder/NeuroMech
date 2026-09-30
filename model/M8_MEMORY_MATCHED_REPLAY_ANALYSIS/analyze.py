#!/usr/bin/env python3
"""Post-result, task-seed-paired comparison of M8 replay and equal-buffer horizons."""
import csv,json,hashlib,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
SOURCE=REPO/'data/results/M8_MEMORY_MATCHED_REPLAY_ANALYSIS/source_M8/task_metrics.csv'
DEFAULT_OUT=ROOT/'results' if ROOT.parent.name=='experiments' else REPO/'data/results/M8_MEMORY_MATCHED_REPLAY_ANALYSIS/reproductions'
OUT=Path(os.environ.get('M8_ANALYSIS_OUT',str(DEFAULT_OUT))); OUT.mkdir(parents=True,exist_ok=False)
rows=list(csv.DictReader(SOURCE.open()))
score={(float(r['rho']),int(r['seed']),int(r['delay']),r['arm']):float(r['accuracy']) for r in rows}
assert len(score)==1350
seeds=range(30); rhos=(0.0,0.5,0.9); delays=(4,16,64)
def contrast(rho,delay,seed):
    return score[(rho,seed,delay,'EXACT_REPLAY')]-score[(rho,seed,delay,f'HORIZON_{delay}')]
per_seed=np.array([np.mean([contrast(rho,d,s) for rho in rhos for d in delays]) for s in seeds])
rng=np.random.default_rng(20261001)
def ci(values):
    values=np.asarray(values); idx=rng.integers(0,len(values),(20000,len(values)))
    boot=values[idx].mean(axis=1)
    return [float(np.quantile(boot,.025)),float(np.quantile(boot,.975))]
summary={'analysis':'M8_MEMORY_MATCHED_REPLAY_ANALYSIS','classification':'post-result exploratory; reuses M8 task outcomes',
 'contrast':'EXACT_REPLAY accuracy minus HORIZON_D accuracy, D × 64 float active feature-history accounting',
 'across_condition':{'mean':float(per_seed.mean()),'task_seed_bootstrap_95ci':ci(per_seed),'positive_seed_count':int((per_seed>0).sum()),'n_task_seeds':30},'by_delay':[],'cells':[]}
for d in delays:
    vals=np.array([np.mean([contrast(rho,d,s) for rho in rhos]) for s in seeds])
    summary['by_delay'].append({'delay':d,'mean':float(vals.mean()),'task_seed_bootstrap_95ci':ci(vals),'positive_seed_count':int((vals>0).sum()),'active_history_float_values_per_arm':d*64})
for rho in rhos:
    for d in delays:
        vals=np.array([contrast(rho,d,s) for s in seeds])
        summary['cells'].append({'rho':rho,'delay':d,'mean_exact_replay_minus_matched_horizon':float(vals.mean()),'task_seed_bootstrap_95ci':ci(vals)})
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (OUT/'per_seed_contrasts.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['seed','exact_replay_minus_matched_horizon']);w.writeheader()
    w.writerows({'seed':i,'exact_replay_minus_matched_horizon':float(v)} for i,v in enumerate(per_seed))
with (OUT/'cell_contrasts.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['rho','delay','mean_exact_replay_minus_matched_horizon','ci_low','ci_high']);w.writeheader()
    for c in summary['cells']:
        w.writerow({'rho':c['rho'],'delay':c['delay'],'mean_exact_replay_minus_matched_horizon':c['mean_exact_replay_minus_matched_horizon'],'ci_low':c['task_seed_bootstrap_95ci'][0],'ci_high':c['task_seed_bootstrap_95ci'][1]})
manifest={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'analysis_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'n_source_rows':len(rows),'n_unique_source_keys':len(score),'numpy':np.__version__,'bootstrap_draws':20000,'bootstrap_seed':20261001,'status':'post-result exploratory analysis'}
(OUT/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(summary,indent=2))

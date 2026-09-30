#!/usr/bin/env python3
"""M7: map delayed-credit benefit against input autocorrelation and objective."""
from __future__ import annotations
import csv, hashlib, json, platform
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data'/'results'/'M7_TEMPORAL_CORRELATION_BOUNDARY'/f"rerun_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
MASTER_SEED=20260930
N_INPUT,N_FEATURES,N_OUTPUT=32,64,4
N_TRAIN,N_TEST=3000,1000
SEEDS=30
RHOS=(0.0,0.2,0.4,0.6,0.8,0.9)
DELAYS=(1,4,16,64)
OBJECTIVES=('CLASSIFICATION','REGRESSION')
ARMS=('EXACT_REPLAY','ELIGIBILITY_TRACE','NO_TRACE')
LR,GAMMA=0.01,0.98
BOOTSTRAPS=20000


def ar1_stream(rng,rho,n):
    x=np.empty((n,N_INPUT),dtype=np.float64)
    x[0]=rng.normal(size=N_INPUT)
    scale=np.sqrt(1-rho*rho)
    for t in range(1,n): x[t]=rho*x[t-1]+scale*rng.normal(size=N_INPUT)
    return x


def make_task(objective,rho,seed):
    oi=OBJECTIVES.index(objective); ri=RHOS.index(rho)
    base=np.random.default_rng(np.random.SeedSequence([MASTER_SEED,oi,seed,101]))
    projection=base.normal(size=(N_INPUT,N_FEATURES))/np.sqrt(N_INPUT)
    teacher=base.normal(size=(N_FEATURES,N_OUTPUT))/np.sqrt(N_FEATURES)
    rng=np.random.default_rng(np.random.SeedSequence([MASTER_SEED,oi,ri,seed,707]))
    raw_train=ar1_stream(rng,rho,N_TRAIN)
    raw_test=ar1_stream(rng,rho,N_TEST)
    phi_train=np.tanh(raw_train@projection)
    phi_test=np.tanh(raw_test@projection)
    phi_train/=np.maximum(np.linalg.norm(phi_train,axis=1,keepdims=True),1e-12)
    phi_test/=np.maximum(np.linalg.norm(phi_test,axis=1,keepdims=True),1e-12)
    linear_train=phi_train@teacher
    linear_test=phi_test@teacher
    if objective=='CLASSIFICATION':
        y_train=np.argmax(linear_train,axis=1)
        y_test=np.argmax(linear_test,axis=1)
    else:
        y_train=linear_train
        y_test=linear_test
    return phi_train,y_train,phi_test,y_test


def softmax(z):
    z=z-np.max(z); e=np.exp(z); return e/e.sum()


def evaluate(w,features,labels,objective):
    pred=features@w
    if objective=='CLASSIFICATION': return float(np.mean(np.argmax(pred,axis=1)==labels))
    return float(np.mean((pred-labels)**2))


def train_one(phi,y,phi_test,y_test,delay,objective,seed,rho):
    weights={a:np.zeros((N_FEATURES,N_OUTPUT),dtype=np.float64) for a in ARMS}
    history={a:[] for a in ARMS}
    eligibility=np.zeros(N_FEATURES)
    for step in range(N_TRAIN+delay):
        has_input=step<N_TRAIN
        feature=phi[step] if has_input else np.zeros(N_FEATURES)
        if has_input:
            for arm in ARMS:
                z=feature@weights[arm]
                history[arm].append(softmax(z) if objective=='CLASSIFICATION' else z.copy())
        eligibility=GAMMA*eligibility+feature
        target_i=step-delay
        if not 0<=target_i<N_TRAIN: continue
        if objective=='CLASSIFICATION':
            target=np.zeros(N_OUTPUT); target[int(y[target_i])]=1.0
        else:
            target=y[target_i]
        for arm in ARMS:
            error=target-history[arm][target_i]
            if arm=='EXACT_REPLAY': update=phi[target_i]
            elif arm=='ELIGIBILITY_TRACE': update=eligibility/max(np.linalg.norm(eligibility),1e-12)
            else: update=feature
            weights[arm]+=LR*np.outer(update,error)
    rows=[]
    for arm in ARMS:
        rows.append({'objective':objective,'rho':rho,'seed':seed,'delay':delay,'arm':arm,
                     'metric_name':'accuracy' if objective=='CLASSIFICATION' else 'mse',
                     'score':evaluate(weights[arm],phi_test,y_test,objective),
                     'n_train':N_TRAIN,'n_test':N_TEST})
    return rows


def bootstrap_ci(values,seed):
    rng=np.random.default_rng(seed); values=np.asarray(values); n=len(values)
    idx=rng.integers(0,n,size=(BOOTSTRAPS,n))
    means=values[idx].mean(axis=1)
    return [float(np.quantile(means,.025)),float(np.quantile(means,.975))]


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    rows=[]
    for objective in OBJECTIVES:
        for rho in RHOS:
            for seed in range(SEEDS):
                phi,y,phi_test,y_test=make_task(objective,rho,seed)
                for delay in DELAYS: rows.extend(train_one(phi,y,phi_test,y_test,delay,objective,seed,rho))
    with (OUT/'task_metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    indexed={(r['objective'],float(r['rho']),int(r['seed']),int(r['delay']),r['arm']):float(r['score']) for r in rows}
    benefit={}
    for obj in OBJECTIVES:
        for rho in RHOS:
            for d in DELAYS:
                vals=[]
                for s in range(SEEDS):
                    trace=indexed[(obj,rho,s,d,'ELIGIBILITY_TRACE')]
                    no=indexed[(obj,rho,s,d,'NO_TRACE')]
                    vals.append(trace-no if obj=='CLASSIFICATION' else no-trace)
                benefit[(obj,rho,d)]=np.array(vals)
    cell_summary=[]
    for obj in OBJECTIVES:
        for rho in RHOS:
            for d in DELAYS:
                b=benefit[(obj,rho,d)]
                replay_gap=[]
                for s in range(SEEDS):
                    tr=indexed[(obj,rho,s,d,'ELIGIBILITY_TRACE')]
                    rp=indexed[(obj,rho,s,d,'EXACT_REPLAY')]
                    replay_gap.append(tr-rp if obj=='CLASSIFICATION' else rp-tr)
                cell_summary.append({'objective':obj,'rho':rho,'delay':d,'trace_benefit_mean':float(b.mean()),
                  'trace_benefit_seed_bootstrap_95ci':bootstrap_ci(b,MASTER_SEED+int(rho*1000)+d+OBJECTIVES.index(obj)*10000),
                  'trace_disadvantage_vs_replay_mean':float(np.mean(replay_gap))})
    # paired seed-level interaction: mean over two objectives and four delays.
    per_seed=np.zeros(SEEDS)
    for obj in OBJECTIVES:
        for d in DELAYS:
            per_seed += benefit[(obj,0.0,d)]-benefit[(obj,0.9,d)]
    per_seed/=len(OBJECTIVES)*len(DELAYS)
    primary={'estimand':'equal-weight mean over objectives and delays of [trace benefit at rho=0 minus trace benefit at rho=0.9]',
      'mean':float(per_seed.mean()),'seed_bootstrap_95ci':bootstrap_ci(per_seed,MASTER_SEED+991),
      'positive_seed_count':int((per_seed>0).sum()),'n_task_seeds':SEEDS,
      'interpretation':'positive means stronger input autocorrelation reduces the relative benefit of explicit eligibility'}
    result={'experiment':'M7_TEMPORAL_CORRELATION_BOUNDARY','classification':'post-result exploratory phase diagram',
      'rho_values':RHOS,'delays':DELAYS,'objectives':OBJECTIVES,'arms':ARMS,'learning_rate':LR,'eligibility_decay':GAMMA,
      'primary':primary,'cells':cell_summary,'n_rows':len(rows),
      'scope':'same random-feature teacher/readout family; two losses and a fixed autocorrelation sweep; no biological validation or algorithm novelty claim'}
    (OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    # One compact per-seed table preserves paired task-seed interactions.
    with (OUT/'primary_seed_contrasts.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['seed','interaction']); writer.writeheader()
        writer.writerows({'seed':s,'interaction':float(per_seed[s])} for s in range(SEEDS))
    manifest={'experiment':'M7_TEMPORAL_CORRELATION_BOUNDARY','seed':MASTER_SEED,'n_seeds':SEEDS,'rho_values':RHOS,
      'delays':DELAYS,'objectives':OBJECTIVES,'arms':ARMS,'training_examples':N_TRAIN,'test_examples':N_TEST,
      'learning_rate':LR,'eligibility_decay':GAMMA,'python':platform.python_version(),'numpy':np.__version__,
      'rows':len(rows),'artifacts':{}}
    for p in [ROOT/'summery'/'M7_TEMPORAL_CORRELATION_BOUNDARY'/'EXPERIMENT_CONTRACT.md',Path(__file__).resolve(),OUT/'task_metrics.csv',OUT/'summary.json',OUT/'primary_seed_contrasts.csv']:
        manifest['artifacts'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'primary':primary,'cells':len(cell_summary)},indent=2))

if __name__=='__main__': main()

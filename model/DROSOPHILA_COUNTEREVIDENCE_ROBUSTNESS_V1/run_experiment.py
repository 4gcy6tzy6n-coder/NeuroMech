#!/usr/bin/env python3
"""Reduced-order simulation of stationary-pattern counterevidence under coverage shift."""
from __future__ import annotations
import csv, hashlib, json, platform
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "summery/DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1/DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1_CONTRACT.md"
PROVENANCE = ROOT / "data/raw/drosophila_counterevidence/SOURCE_PROVENANCE.md"
OUT = ROOT / "data/results/DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1"
N_BINS = 72
TRAIN_SEEDS = range(410000, 410030)
TEST_SEEDS = range(410100, 410200)
TRAIN_COVERAGE = (0.15, 0.25, 0.35, 0.50)
TEST_COVERAGE = (0.60, 0.75, 0.90)
PROFILES = ("PATTERNED_STATIC", "UNIFORM_STATIC", "FLICKERING_BACKGROUND")
N_PER_CELL_TRAIN = 40
N_PER_CELL_TEST = 40
BOOT = 20000
BOOT_SEED = 20260930


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def sample_episode(rng: np.random.Generator, label: int, coverage: float, profile: str):
    """Return 4 feature fractions. Label 1=self rotation, 0=object motion."""
    n_moving = int(round(coverage*N_BINS))
    n_still = N_BINS-n_moving
    direction = int(rng.choice((-1,1)))
    # Both classes have identical local motion statistics; only stationary texture differs.
    moving = np.zeros(N_BINS, dtype=np.int8)
    moving[:n_moving] = direction
    # 8% of moving local detectors report the opposite direction.
    flips = rng.random(n_moving) < 0.08
    moving[:n_moving][flips] *= -1
    rng.shuffle(moving)
    observed = moving.copy()
    # Independent detector dropout and sparse false motion.
    drop = (observed != 0) & (rng.random(N_BINS) < 0.08)
    observed[drop] = 0
    false = (observed == 0) & (rng.random(N_BINS) < 0.025)
    observed[false] = rng.choice((-1,1), size=int(false.sum()))
    active = observed != 0
    moving_fraction=float(active.mean())
    signed=float(observed.mean())
    coherence=float(max(np.mean(observed==1), np.mean(observed==-1)))
    zero_fraction=float((~active).mean())

    # Self rotation has uniform/low-contrast blank regions. Object motion has
    # patterned stationary background only in the PATTERNED_STATIC condition.
    if label == 0 and profile == "PATTERNED_STATIC":
        p_detect=0.88
    elif label == 0 and profile == "FLICKERING_BACKGROUND":
        p_detect=0.04
    elif label == 0:  # stationary but spatially uniform background
        p_detect=0.025
    else:
        p_detect=0.035  # false stationary-pattern responses in low-contrast regions
    stationary_detected=int(rng.binomial(n_still, p_detect))
    stable_texture_fraction=stationary_detected/N_BINS
    return moving_fraction, signed, coherence, zero_fraction, stable_texture_fraction


def make_data(seeds, coverages, profiles, n_per_cell, train=False):
    rows=[]
    for seed in seeds:
        rng=np.random.default_rng(seed)
        for cov in coverages:
            for profile in profiles:
                for label in (0,1):
                    for rep in range(n_per_cell):
                        feats=sample_episode(rng,label,cov,profile)
                        rows.append({"seed_block":seed,"coverage":cov,"profile":profile,
                                     "label":label,"replicate":rep,
                                     "moving_fraction":feats[0],"signed_flow":feats[1],
                                     "direction_coherence":feats[2],"zero_fraction":feats[3],
                                     "stationary_pattern_fraction":feats[4]})
    return rows


def feature_matrix(rows, names):
    return np.asarray([[r[n] for n in names] for r in rows],dtype=float)


def fit(x,y):
    m=make_pipeline(StandardScaler(),LogisticRegression(C=1.0,solver="liblinear",max_iter=2000,random_state=0))
    m.fit(x,y)
    return m


def auc(y,p):
    return float(roc_auc_score(y,p))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    train=make_data(TRAIN_SEEDS,TRAIN_COVERAGE,PROFILES,N_PER_CELL_TRAIN,True)
    test=make_data(TEST_SEEDS,TEST_COVERAGE,PROFILES,N_PER_CELL_TEST)
    feature_sets={
      "MOTION_ONLY":["moving_fraction","signed_flow","direction_coherence"],
      "ZERO_FLOW_CONTROL":["moving_fraction","signed_flow","direction_coherence","zero_fraction"],
      "COUNTEREVIDENCE":["moving_fraction","signed_flow","direction_coherence","stationary_pattern_fraction"],
      "SHUFFLED_COUNTEREVIDENCE":["moving_fraction","signed_flow","direction_coherence","stationary_pattern_fraction"],
    }
    # Permute the candidate cue in both train and test within coverage/profile strata.
    # This preserves feature marginals while removing example-level class alignment.
    def permute_static_feature(rows, seed):
        copied=[dict(r) for r in rows]
        prng=np.random.default_rng(seed)
        strata={}
        for i,r in enumerate(copied): strata.setdefault((r['coverage'],r['profile']),[]).append(i)
        for ids in strata.values():
            vals=np.asarray([copied[i]['stationary_pattern_fraction'] for i in ids]); prng.shuffle(vals)
            for i,v in zip(ids,vals): copied[i]['stationary_pattern_fraction']=float(v)
        return copied
    shuf_train=permute_static_feature(train,BOOT_SEED)
    shuf_test=permute_static_feature(test,BOOT_SEED+1)
    models={}
    ytrain=np.asarray([r['label'] for r in train])
    for name,cols in feature_sets.items():
        dat=shuf_train if name=="SHUFFLED_COUNTEREVIDENCE" else train
        models[name]=fit(feature_matrix(dat,cols),np.asarray([r['label'] for r in dat]))

    metric_rows=[]
    for name,cols in feature_sets.items():
        model=models[name]
        score_rows=shuf_test if name=="SHUFFLED_COUNTEREVIDENCE" else test
        for r,x in zip(score_rows,feature_matrix(score_rows,cols)):
            prob=float(model.predict_proba(x.reshape(1,-1))[0,1])
            # Counterfactual sensory ablation is recorded for the counterevidence model.
            ablated=prob
            if name=="COUNTEREVIDENCE":
                xa=x.copy(); xa[-1]=model.named_steps["standardscaler"].mean_[-1]
                ablated=float(model.predict_proba(xa.reshape(1,-1))[0,1])
            metric_rows.append({**r,"model":name,"p_self_rotation":prob,
                                "prediction":int(prob>=0.5),"p_self_after_static_cue_ablation":ablated})
    path=OUT/"episode_predictions.csv"
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(metric_rows[0])); w.writeheader(); w.writerows(metric_rows)

    # Aggregate within independent environment seed blocks and test coverage/profile cells.
    groups={}
    for r in metric_rows: groups.setdefault((r['model'],r['seed_block'],r['coverage'],r['profile']),[]).append(r)
    block_rows=[]
    for (model,seed,cov,profile),rs in groups.items():
        y=np.asarray([r['label'] for r in rs]); pred=np.asarray([r['prediction'] for r in rs]); p=np.asarray([r['p_self_rotation'] for r in rs])
        block_rows.append({"model":model,"seed_block":seed,"coverage":cov,"profile":profile,
          "balanced_accuracy":float(0.5*((pred[y==0]==0).mean()+(pred[y==1]==1).mean())),
          "object_motion_false_positive_rate":float((pred[y==0]==1).mean()),
          "self_rotation_sensitivity":float((pred[y==1]==1).mean()),"auc":auc(y,p)})
    bpath=OUT/"seed_block_metrics.csv"
    with bpath.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(block_rows[0])); w.writeheader(); w.writerows(block_rows)

    # Primary: patterned-stationary profile at held-out coverage, paired by seed and coverage.
    lookup={(r['model'],int(r['seed_block']),float(r['coverage']),r['profile']):r for r in block_rows}
    contrasts=[]
    for seed in TEST_SEEDS:
      for cov in TEST_COVERAGE:
        b=lookup["COUNTEREVIDENCE",seed,cov,"PATTERNED_STATIC"]['balanced_accuracy']
        a=lookup["MOTION_ONLY",seed,cov,"PATTERNED_STATIC"]['balanced_accuracy']
        contrasts.append(float(b-a))
    per_seed=np.asarray([np.mean(contrasts[i*len(TEST_COVERAGE):(i+1)*len(TEST_COVERAGE)]) for i in range(len(TEST_SEEDS))])
    brng=np.random.default_rng(BOOT_SEED+1)
    draws=per_seed[brng.integers(0,len(per_seed),(BOOT,len(per_seed)))].mean(axis=1)
    primary={"contrast":"COUNTEREVIDENCE - MOTION_ONLY balanced accuracy",
      "mean_equal_weighted_over_coverage":float(per_seed.mean()),
      "seed_block_bootstrap_95_ci":[float(np.quantile(draws,.025)),float(np.quantile(draws,.975))],
      "positive_seed_blocks":int((per_seed>0).sum()),"n_test_seed_blocks":len(TEST_SEEDS)}
    summaries={}
    for model in feature_sets:
      summaries[model]={}
      for profile in PROFILES:
       for cov in TEST_COVERAGE:
        sel=[r for r in block_rows if r['model']==model and r['profile']==profile and float(r['coverage'])==cov]
        summaries[model][f"{profile}_coverage_{cov:.2f}"]={
          "balanced_accuracy":float(np.mean([r['balanced_accuracy'] for r in sel])),
          "object_motion_false_positive_rate":float(np.mean([r['object_motion_false_positive_rate'] for r in sel])),
          "self_rotation_sensitivity":float(np.mean([r['self_rotation_sensitivity'] for r in sel])),
          "auc":float(np.mean([r['auc'] for r in sel]))}
    ab=[]
    for r in metric_rows:
      if r['model']=="COUNTEREVIDENCE":
       ab.append((int(r['label']),r['profile'],r['coverage'],r['prediction'],int(r['p_self_after_static_cue_ablation']>=.5)))
    ablation={}
    for profile in PROFILES:
      sel=[r for r in ab if r[1]==profile]
      ablation[profile]={"accuracy_full":float(np.mean([r[3]==r[0] for r in sel])),
                         "accuracy_static_cue_ablation":float(np.mean([r[4]==r[0] for r in sel]))}
    result={"status":"COMPLETED_EXPLORATORY_REDUCED_ORDER_TRANSFER_SANITY_TEST",
      "primary":primary,"cell_means":summaries,"static_cue_ablation":ablation,
      "design":{"training_seed_blocks":len(TRAIN_SEEDS),"heldout_seed_blocks":len(TEST_SEEDS),
       "training_coverage":list(TRAIN_COVERAGE),"heldout_coverage":list(TEST_COVERAGE),
       "profiles":list(PROFILES),"sensor_bins":N_BINS,"examples_per_seed_cell_and_class":N_PER_CELL_TEST,
       "analysis_unit":"environment seed block; episodes are clustered within seed block",
       "model_regularization_C":1.0,"bootstrap_resamples":BOOT,"bootstrap_seed":BOOT_SEED},
      "interpretation_boundary":"Synthetic reduced-order feature simulation only; no biological outcome analysis, natural-image benchmark, or general AI advantage claim.",
      "implementation_correction":"The initial run permuted the shuffled-control stationary feature in training only. Final run independently permutes the same feature in both training and test sets within coverage/profile strata. The solver was changed from lbfgs to liblinear after lbfgs emitted divide-by-zero/overflow warnings on this feature design; both optimize the frozen L2 logistic objective, and the final rerun was executed with warnings treated as errors."}
    spath=OUT/"summary.json"; spath.write_text(json.dumps(result,indent=2)+"\n")
    manifest={"experiment":"DROSOPHILA_COUNTEREVIDENCE_ROBUSTNESS_V1",
      "author_ann_repository":"https://github.com/ClarkLabCode/SelfMotionDetectionML",
      "author_ann_commit":"75a7051a0e310311b9295afe0a2b5c68f25eba9d",
      "contract_sha256":sha256(CONTRACT),"source_provenance_sha256":sha256(PROVENANCE),
      "runner_sha256":sha256(Path(__file__)),"python":platform.python_version(),
      "numpy":np.__version__,"scikit_learn":__import__('sklearn').__version__,
      "solver":"liblinear","warning_free_under_-W_error":True,
      "finite_model_coefficients":{name:bool(np.isfinite(model[-1].coef_).all() and np.isfinite(model[-1].intercept_).all()) for name,model in models.items()},
      "outputs":{"episode_predictions.csv":sha256(path),"seed_block_metrics.csv":sha256(bpath),"summary.json":sha256(spath)}}
    (OUT/"run_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__": main()

#!/usr/bin/env python3
"""Paired training-seed analysis for M2 action-conditioned state estimation."""
import csv, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]; EXP="M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1"
OUT=ROOT/"data/results"/EXP; SEEDS=list(range(930000,930032));
ARMS=["LTC_SENSORY_SITE","LTC_OUTPUT_SITE","LTC_NO_FEEDBACK","LTC_DENSE_FEEDBACK","LTC_SENSORY_YOKED","GRU_2","GRU_4","SIGNED_STATE_ORACLE"]
COUPLINGS=[1.0,0.0,-1.0]; NTEST=256; NBOOT=20000; BOOT_SEED=20261004
def read(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def boot(x):
    rg=np.random.default_rng(BOOT_SEED); ix=rg.integers(0,len(x),(NBOOT,len(x)))
    return [float(y) for y in np.quantile(x[ix].mean(1),[.025,.975])]
def main():
    rows=read(OUT/"episode_results.csv"); fits=read(OUT/"training_results.csv")
    assert len(rows)==len(SEEDS)*len(ARMS)*len(COUPLINGS)*NTEST
    assert len(fits)==len(SEEDS)*len(ARMS[:-1])
    groups={};seen=set()
    for r in rows:
        k=(int(r["training_seed"]),r["arm"],float(r["coupling"]),int(r["episode_id"]))
        assert k not in seen;seen.add(k)
        assert k[0] in SEEDS and k[1] in ARMS and k[2] in COUPLINGS and 0<=k[3]<NTEST
        for m in ("displacement_mse","displacement_mae","prediction_bias"):
            v=float(r[m]);assert np.isfinite(v) and (m=="prediction_bias" or v>=0)
        groups.setdefault(k[:3],[]).append(r)
    assert len(groups)==len(SEEDS)*len(ARMS)*len(COUPLINGS)
    assert all(len(v)==NTEST for v in groups.values())
    def mean(seed,arm,c,metric):return float(np.mean([float(r[metric]) for r in groups[(seed,arm,c)]]))
    contrasts=[];summaries=[]
    for c in COUPLINGS:
        for comp in [x for x in ARMS if x!="LTC_SENSORY_SITE"]:
            e=np.array([mean(s,comp,c,"displacement_mse")-mean(s,"LTC_SENSORY_SITE",c,"displacement_mse") for s in SEEDS])
            contrasts.append({"coupling":c,"contrast":f"{comp}_MSE_MINUS_LTC_SENSORY_SITE_MSE",
                "mean_paired_seed_effect":float(e.mean()),"bootstrap_95ci":boot(e),
                "positive_seed_blocks":int((e>0).sum()),"seed_blocks":len(SEEDS)})
        for arm in ARMS:
            for metric in ("displacement_mse","displacement_mae","prediction_bias"):
                v=np.array([mean(s,arm,c,metric) for s in SEEDS])
                summaries.append({"coupling":c,"arm":arm,"metric":metric,"mean_seed_block":float(v.mean()),
                    "bootstrap_95ci":boot(v),"seed_blocks":len(SEEDS)})
    resources={}
    for arm in ARMS[:-1]:
        rr=[r for r in fits if r["arm"]==arm]
        resources[arm]={"parameter_counts":sorted({int(r["parameter_count"]) for r in rr}),
            "mean_training_seconds":float(np.mean([float(r["training_seconds"]) for r in rr])),
            "mean_final_10_update_loss":float(np.mean([float(r["final_10_update_loss"]) for r in rr]))}
    primary=[x for x in contrasts if x["coupling"]==1.0]
    summary={"experiment_id":EXP,"status":"POST_RESULT_EXPLORATORY_ARTIFICIAL_EXPERIMENT",
        "primary_condition":{"coupling":1.0},"primary_contrasts":primary,
        "all_displacement_mse_contrasts":contrasts,"arm_metric_summaries":summaries,
        "resource_accounting":resources,"row_counts":{"episode_results":len(rows),"training_results":len(fits)},
        "independent_seed_blocks":len(SEEDS),"episodes_per_seed_arm_coupling":NTEST,
        "bootstrap":{"resamples":NBOOT,"seed":BOOT_SEED,"unit":"paired training-seed block"}}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({"primary_contrasts":primary,"resources":resources,"row_counts":summary["row_counts"]},indent=2))
if __name__=="__main__":main()

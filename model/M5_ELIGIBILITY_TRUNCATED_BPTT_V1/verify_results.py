#!/usr/bin/env python3
"""Independent structural and paired-bootstrap verification."""
import csv,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];EXP="M5_ELIGIBILITY_TRUNCATED_BPTT_V1";OUT=ROOT/"data/results"/EXP
CONTRACT=ROOT/"summery"/EXP/"CONTRACT.md";RUNNER=Path(__file__).with_name("run_experiment.py")
SEEDS=list(range(2000,2032));ARMS=["ELIGIBILITY_TRACE","NO_TRACE","TBPTT_1","TBPTT_4","BPTT_FULL"]
BOOT,BOOT_SEED=20000,20261013
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ci(v):
    rng=np.random.default_rng(BOOT_SEED);ix=rng.integers(0,len(v),(BOOT,len(v)));return [float(x) for x in np.quantile(v[ix].mean(1),[.025,.975])]
def main():
    manifest=json.loads((OUT/"run_manifest.json").read_text());pre=json.loads((OUT/"PREFLIGHT.json").read_text());summary=json.loads((OUT/"summary.json").read_text())
    assert manifest["contract_sha256"]==sha(CONTRACT) and manifest["runner_sha256"]==sha(RUNNER)
    assert pre["contract_sha256"]==sha(CONTRACT) and pre["runner_sha256"]==sha(RUNNER) and pre["outcomes_computed"] is False
    with (OUT/"task_seed_results.csv").open(newline="") as f:rows=list(csv.DictReader(f))
    assert len(rows)==len(SEEDS)*len(ARMS)==160
    table={}
    for r in rows:
        k=(int(r["task_seed"]),r["arm"]);assert k not in table and k[0] in SEEDS and k[1] in ARMS
        assert int(r["parameter_count"])==746 and int(r["train_episodes"])==3000 and int(r["test_episodes"])==500
        for m in ("accuracy","cross_entropy","training_seconds"):
            z=float(r[m]);assert np.isfinite(z) and z>=0
        assert 0<=float(r["accuracy"])<=1;table[k]=r
    for s in SEEDS:assert all((s,a) in table for a in ARMS)
    contrasts={}
    for arm in ARMS:
        if arm=="ELIGIBILITY_TRACE":continue
        v=np.array([float(table[(s,"ELIGIBILITY_TRACE")]["accuracy"])-float(table[(s,arm)]["accuracy"]) for s in SEEDS])
        result=next(x for x in summary["contrasts"] if x["contrast"]==f"ELIGIBILITY_TRACE_MINUS_{arm}")
        assert abs(v.mean()-result["mean_accuracy_difference"])<1e-12 and np.allclose(ci(v),result["bootstrap_95ci"],atol=1e-12)
        assert int((v>0).sum())==result["positive_seeds"];contrasts[arm]={"mean":float(v.mean()),"ci95":ci(v)}
    b=np.array([float(table[(s,"BPTT_FULL")]["accuracy"]) for s in SEEDS]);v=summary["full_bptt_viability"]
    assert np.allclose(ci(b),v["bootstrap_95ci"],atol=1e-12) and bool(ci(b)[0]>.5)==bool(v["viable"])
    for name,digest in manifest["output_sha256"].items():assert sha(OUT/name)==digest
    figs=[OUT/"figures"/f"{EXP}.{ext}" for ext in ("png","svg","pdf")]
    assert all(p.exists() and p.stat().st_size>0 for p in figs)
    report={"experiment_id":EXP,"passed":True,"checks":{"complete_seed_arm_grid":True,"parameter_counts_and_rows_valid":True,
        "paired_effects_and_bootstraps_recomputed":True,"full_bptt_viability_recomputed":True,"input_hashes_valid":True,"figures_present":True},
        "n_rows":len(rows),"primary_trace_minus_tbptt4":contrasts["TBPTT_4"],"full_bptt_viability_ci95":ci(b)}
    (OUT/"POSTRUN_VERIFICATION.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2))
if __name__=="__main__":main()

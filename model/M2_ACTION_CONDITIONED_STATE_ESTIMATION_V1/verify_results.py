#!/usr/bin/env python3
"""Check completeness and independently recompute primary contrasts."""
import csv,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];EXP="M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1";OUT=ROOT/"data/results"/EXP
SEEDS=list(range(930000,930032));ARMS=["LTC_SENSORY_SITE","LTC_OUTPUT_SITE","LTC_NO_FEEDBACK","LTC_DENSE_FEEDBACK","LTC_SENSORY_YOKED","GRU_2","GRU_4","SIGNED_STATE_ORACLE"]
COUPLINGS=[1.,0.,-1.];N=256
def read(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ep=read(OUT/"episode_results.csv");fits=read(OUT/"training_results.csv");s=json.loads((OUT/"summary.json").read_text())
    pre=json.loads((OUT/"PREFLIGHT.json").read_text());meta=json.loads((OUT/"RUN_METADATA.json").read_text())
    runner=ROOT/"model"/EXP/"run_experiment.py";contract=ROOT/"summery"/EXP/"CONTRACT.md"
    assert pre["contract_sha256"]==meta["contract_sha256"]==sha(contract)
    assert pre["runner_sha256"]==meta["runner_sha256"]==sha(runner)
    assert len(ep)==len(SEEDS)*len(ARMS)*len(COUPLINGS)*N==196608
    assert len(fits)==len(SEEDS)*7==224
    keys=set();groups={}
    for r in ep:
        k=(int(r["training_seed"]),r["arm"],float(r["coupling"]),int(r["episode_id"]))
        assert k not in keys;keys.add(k)
        assert k[0] in SEEDS and k[1] in ARMS and k[2] in COUPLINGS and 0<=k[3]<N
        for m in ("displacement_mse","displacement_mae","prediction_bias"):
            v=float(r[m]);assert np.isfinite(v) and (m=="prediction_bias" or v>=0)
        groups.setdefault(k[:3],[]).append(r)
    assert len(groups)==len(SEEDS)*len(ARMS)*len(COUPLINGS) and all(len(v)==N for v in groups.values())
    pcounts={}
    for r in fits:
        arm=r["arm"];pcounts.setdefault(arm,set()).add(int(r["parameter_count"]))
        assert int(r["updates"])==160 and float(r["training_seconds"])>0
        assert np.isfinite([float(r["initial_loss"]),float(r["final_10_update_loss"]) ]).all()
    assert pcounts=={"LTC_SENSORY_SITE":{42},"LTC_OUTPUT_SITE":{42},"LTC_NO_FEEDBACK":{42},"LTC_DENSE_FEEDBACK":{42},"LTC_SENSORY_YOKED":{42},"GRU_2":{45},"GRU_4":{113}}
    keyed={}
    for r in ep:keyed.setdefault((int(r["training_seed"]),r["arm"],float(r["coupling"])),[]).append(float(r["displacement_mse"]))
    for r in s["primary_contrasts"]:
        comp=r["contrast"].split("_MSE_MINUS_LTC_SENSORY_SITE_MSE")[0]
        diffs=[np.mean(keyed[(seed,comp,1.)])-np.mean(keyed[(seed,"LTC_SENSORY_SITE",1.)]) for seed in SEEDS]
        assert abs(float(np.mean(diffs))-r["mean_paired_seed_effect"])<1e-10
    figs=[OUT/"figures"/f"{EXP}.{x}" for x in ("png","svg","pdf")];assert all(p.exists() and p.stat().st_size for p in figs)
    report={"experiment_id":EXP,"passed":True,"checks":{"seed_arm_condition_grid_complete":True,"no_duplicate_episodes":True,
        "finite_metrics":True,"training_records_and_parameter_counts_valid":True,"primary_point_estimates_recomputed":True,"figures_present":True},
        "row_counts":{"episode_results":len(ep),"training_results":len(fits)},"input_sha256":{p.name:sha(p) for p in (OUT/"episode_results.csv",OUT/"training_results.csv",OUT/"summary.json")}}
    (OUT/"POSTRUN_VERIFICATION.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2))
if __name__=="__main__":main()

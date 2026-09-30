#!/usr/bin/env python3
"""Summarize the paired context-information dose response and bootstrap uncertainty."""
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
SEEDS=np.arange(43000,43030)
KAPPAS=np.round(np.arange(-.5,.5001,.1),2)
POLICIES=("MODE_GAIN_FILTER","CONSTANT_GAIN_FILTER","GENERIC_RNN_1D","BILINEAR_RNN_1D","KALMAN_ORACLE")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def boot_seed_means(values, seed, reps=10000):
    rng=np.random.default_rng(seed); n=values.size
    draws=values[rng.integers(0,n,(reps,n))].mean(axis=1)
    return np.quantile(draws,[.025,.975]).tolist()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--results-dir",type=Path,default=ROOT/"data/results/M2_CONTEXT_INFORMATION_DOSE_V1/canonical"); d=ap.parse_args().results_dir.resolve()
    manifest=json.loads((d/"run_manifest.json").read_text()); assert sha(d/"episode_metrics.csv")==manifest["files"]["episode_metrics.csv"]
    arr=np.full((len(SEEDS),len(KAPPAS),256,len(POLICIES)),np.nan,np.float64)
    pidx={p:i for i,p in enumerate(POLICIES)}; kidx={f"{k:.2f}":i for i,k in enumerate(KAPPAS)}; sidx={int(s):i for i,s in enumerate(SEEDS)}
    with (d/"episode_metrics.csv").open() as f:
        for r in csv.DictReader(f): arr[sidx[int(r["train_seed"])],kidx[r["kappa"]],int(r["episode_id"]),pidx[r["policy"]]]=float(r["episode_mse"])
    assert np.isfinite(arr).all() and (arr>=0).all()
    curve=[]; seed_contrasts=[]; primary_cube=np.full((len(SEEDS),256,len(KAPPAS)),np.nan)
    for ki,k in enumerate(KAPPAS):
        mode=arr[:,ki,:,pidx["MODE_GAIN_FILTER"]]; const=arr[:,ki,:,pidx["CONSTANT_GAIN_FILTER"]]
        primary=const-mode
        primary_cube[:,:,ki]=primary
        rng=np.random.default_rng(72061+ki); boot=np.empty(10000)
        for start in range(0,len(boot),128):
            n=min(128,len(boot)-start); si=rng.integers(0,len(SEEDS),(n,len(SEEDS))); ei=rng.integers(0,256,(n,256))
            boot[start:start+n]=primary[si[:,:,None],ei[:,None,:]].mean(axis=(1,2))
        row={"kappa":float(k),"mode_gain_mse":float(mode.mean()),"constant_gain_mse":float(const.mean()),"constant_minus_mode":float(primary.mean()),"crossed_95ci":[float(x) for x in np.quantile(boot,[.025,.975])],"positive_training_seeds":int((primary.mean(axis=1)>0).sum())}
        for p in ("GENERIC_RNN_1D","BILINEAR_RNN_1D","KALMAN_ORACLE"):
            diff=arr[:,ki,:,pidx[p]]-mode
            row[f"{p.lower()}_minus_mode_mse"]=float(diff.mean())
            row[f"{p.lower()}_seed_bootstrap_95ci"]=boot_seed_means(diff.mean(axis=1),83001+ki*10+pidx[p])
        curve.append(row)
        for si,s in enumerate(SEEDS): seed_contrasts.append({"train_seed":int(s),"kappa":float(k),"constant_minus_mode_mse":float(primary[si].mean())})
    crossings=[]
    for a,b in zip(curve,curve[1:]):
        ya,yb=a["constant_minus_mode"],b["constant_minus_mode"]
        if ya==0: crossings.append(a["kappa"])
        elif ya*yb<0: crossings.append(float(a["kappa"]-ya*(b["kappa"]-a["kappa"])/(yb-ya)))
    focal={str(k):next(r for r in curve if abs(r["kappa"]-k)<1e-9) for k in (-.2,0,.2)}
    # Crossed-bootstrap uncertainty for the first upward zero crossing of the full dose curve.
    rng=np.random.default_rng(930071); crossing_boot=[]
    for start in range(0,10000,32):
        n=min(32,10000-start); si=rng.integers(0,len(SEEDS),(n,len(SEEDS))); ei=rng.integers(0,256,(n,256))
        means=primary_cube[si[:,:,None],ei[:,None,:],:].mean(axis=(1,2))
        for vals in means:
            found=None
            for j in range(len(KAPPAS)-1):
                if vals[j] <= 0 < vals[j+1]:
                    found=float(KAPPAS[j]-vals[j]*(KAPPAS[j+1]-KAPPAS[j])/(vals[j+1]-vals[j])); break
            if found is not None: crossing_boot.append(found)
    crossing_ci=np.quantile(crossing_boot,[.025,.975]).tolist() if crossing_boot else None
    result={"experiment_id":"M2_CONTEXT_INFORMATION_DOSE_V1","analysis":"paired held-out episodes; crossed bootstrap resamples train seeds and test episodes","bootstrap_replicates":10000,"primary":"MSE(CONSTANT_GAIN_FILTER)-MSE(MODE_GAIN_FILTER); positive favors mode-gain","rows":len(SEEDS)*len(KAPPAS)*256*len(POLICIES),"focal_estimates":focal,"zero_crossings_linear_interpolation":crossings,"zero_crossing_crossed_bootstrap_95ci":crossing_ci,"zero_crossing_bootstrap_fraction_with_crossing":len(crossing_boot)/10000,"dose_curve":curve}
    (d/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    with (d/"seed_contrasts.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(seed_contrasts[0]),lineterminator="\n");w.writeheader();w.writerows(seed_contrasts)
    manifest["files"]["summary.json"]=sha(d/"summary.json");manifest["files"]["seed_contrasts.csv"]=sha(d/"seed_contrasts.csv")
    manifest["analysis_source_sha256"]={"runner":sha(Path(__file__).with_name("run_experiment.py")),"analyzer":sha(Path(__file__)),"verifier":sha(Path(__file__).with_name("verify_results.py")),"contract":sha(ROOT/"summery/M2_CONTEXT_INFORMATION_DOSE_V1/CONTRACT.md")}
    (d/"run_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"focal_estimates":focal,"zero_crossings":crossings,"rows":result["rows"]},indent=2))
if __name__=="__main__":main()

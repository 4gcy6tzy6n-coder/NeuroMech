#!/usr/bin/env python3
"""Plot seed-block accuracy with percentile bootstrap intervals."""
import csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];EXP="M5_ELIGIBILITY_TRUNCATED_BPTT_V1";OUT=ROOT/"data/results"/EXP
SEEDS=list(range(2000,2032));ARMS=["ELIGIBILITY_TRACE","NO_TRACE","TBPTT_1","TBPTT_4","BPTT_FULL"]
LABELS=["Eligibility trace","No trace","TBPTT-1","TBPTT-4","Full BPTT"];COLORS=["#0072B2","#999999","#56B4E9","#D55E00","#333333"]
def main():
    with (OUT/"task_seed_results.csv").open(newline="") as f:rows=list(csv.DictReader(f))
    rng=np.random.default_rng(20261013);fig,ax=plt.subplots(figsize=(7.2,4.2))
    for i,(arm,label,color) in enumerate(zip(ARMS,LABELS,COLORS)):
        v=np.array([float(next(r["accuracy"] for r in rows if int(r["task_seed"])==s and r["arm"]==arm)) for s in SEEDS])
        ix=rng.integers(0,len(v),(20000,len(v)));lo,hi=np.quantile(v[ix].mean(1),[.025,.975]);m=v.mean()
        ax.bar(i,m,color=color,width=.68,edgecolor="#333333",linewidth=.4);ax.errorbar(i,m,yerr=[[m-lo],[hi-m]],fmt="none",ecolor="black",capsize=4,lw=1)
        for j,val in enumerate(v):ax.scatter(i+(j%8-3.5)*.035,val,s=8,color="#202020",alpha=.55,zorder=3)
    ax.axhline(.5,color="#666666",ls="--",lw=.9)
    ax.text(4.72,.507,"Chance",ha="right",va="bottom",color="#333333",fontsize=8,
            bbox={"facecolor":"white","edgecolor":"none","pad":1.5})
    ax.set_xticks(range(len(ARMS)),LABELS);ax.set_ylabel("Held-out XOR accuracy");ax.set_ylim(.45,1.02)
    ax.set_title("Local eligibility versus truncated recurrent credit assignment");ax.grid(axis="y",color="#dddddd",lw=.6);ax.spines[["top","right"]].set_visible(False)
    ax.set_xlim(-.5,4.8);fig.text(.5,-.01,"32 task-seed blocks; error bars are percentile 95% seed-block bootstrap intervals.",ha="center",fontsize=8)
    fig.tight_layout(rect=(0,.05,1,1));d=OUT/"figures";d.mkdir(parents=True,exist_ok=True)
    for ext,kw in (("png",{"dpi":300}),("svg",{}),("pdf",{})):fig.savefig(d/f"{EXP}.{ext}",bbox_inches="tight",**kw)
    p=d/f"{EXP}.svg";p.write_text("\n".join(x.rstrip() for x in p.read_text().splitlines())+"\n");plt.close(fig)
if __name__=="__main__":main()

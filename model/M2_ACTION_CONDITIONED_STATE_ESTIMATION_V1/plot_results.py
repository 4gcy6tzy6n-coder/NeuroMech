#!/usr/bin/env python3
"""Plot held-out state-estimation error by action/state coupling."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];EXP="M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1"
SUMMARY=ROOT/"data/results"/EXP/"summary.json";OUT=ROOT/"data/results"/EXP/"figures"
ARMS=["LTC_SENSORY_SITE","LTC_OUTPUT_SITE","LTC_NO_FEEDBACK","LTC_DENSE_FEEDBACK","LTC_SENSORY_YOKED","GRU_2","GRU_4"]
LABELS=["LTC sensory-site","LTC output-site","LTC no feedback","LTC dense","LTC yoked","GRU-2","GRU-4"]
COLORS=["#0072B2","#D55E00","#009E73","#CC79A7","#56B4E9","#E69F00","#333333"]
COUPLINGS=[1.,0.,-1.]
def main():
    s=json.loads(SUMMARY.read_text());rows=s["arm_metric_summaries"];OUT.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(7.4,4.1))
    for arm,label,color in zip(ARMS,LABELS,COLORS):
        rs=[next(x for x in rows if x["arm"]==arm and x["metric"]=="displacement_mse" and x["coupling"]==c) for c in COUPLINGS]
        y=[x["mean_seed_block"] for x in rs];lo=[x["bootstrap_95ci"][0] for x in rs];hi=[x["bootstrap_95ci"][1] for x in rs]
        x=range(3);ax.plot(x,y,color=color,marker="o",lw=1.8,label=label);ax.fill_between(x,lo,hi,color=color,alpha=.12,lw=0)
    ax.set_xticks(range(3),["aligned (+1)","no coupling (0)","reversed (−1)"])
    ax.set_ylabel("Signed displacement MSE (lower is better)");ax.set_xlabel("Action-to-state coupling at evaluation")
    ax.set_title("Motor-state input and hidden-state estimation");ax.grid(axis="y",color="#dddddd",lw=.6);ax.spines[["top","right"]].set_visible(False)
    ax.legend(frameon=False,ncol=2,fontsize=8,loc="best")
    fig.text(.5,-.01,"32 training-seed blocks; ribbons are percentile 95% bootstrap intervals. Privileged oracle omitted.",ha="center",fontsize=8)
    fig.tight_layout(rect=(0,.06,1,1))
    for ext,kw in (("png",{"dpi":300}),("svg",{}),("pdf",{})):fig.savefig(OUT/f"{EXP}.{ext}",bbox_inches="tight",**kw)
    p=OUT/f"{EXP}.svg";p.write_text("\n".join(q.rstrip() for q in p.read_text().splitlines())+"\n");plt.close(fig)
if __name__=="__main__":main()

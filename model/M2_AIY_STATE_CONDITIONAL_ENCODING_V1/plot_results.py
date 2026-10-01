#!/usr/bin/env python3
"""Plot animal-level state decoding from AIY and AVA source traces."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
EXP="M2_AIY_STATE_CONDITIONAL_ENCODING_V1"
OUT=ROOT/"data/results"/EXP
df=pd.read_csv(OUT/"animal_results.csv")
colors={"WT":"#2477a5","RIM_ABLATED":"#cf6a3b"}
fig,axes=plt.subplots(1,2,figsize=(8.1,3.7),layout="constrained")
for ax,metric,title in [
    (axes[0],"aiy_only_auc","AIY alone"),
    (axes[1],"aiy_increment_over_previous_state_auc","AIY added beyond previous motor state")]:
    for gi,group in enumerate(["WT","RIM_ABLATED"]):
        y=df.loc[df.group==group,metric].to_numpy()
        x=gi+0.0
        jitter=[-0.10,-0.05,0.0,0.05,0.10]
        ax.scatter([x+j for j in jitter],y,color=colors[group],edgecolor="white",linewidth=.7,s=48,zorder=3)
        ax.plot([x-.16,x+.16],[y.mean(),y.mean()],color="#222222",linewidth=2.0,zorder=4)
    ax.set_xticks([0,1],["WT","RIM ablated"])
    ax.set_title(title,fontsize=10)
    ax.grid(axis="y",color="#dddddd",linewidth=.7)
    ax.spines[["top","right"]].set_visible(False)
axes[0].axhline(.5,color="#777777",linestyle="--",linewidth=1)
axes[0].set_ylabel("Held-out ROC AUC")
axes[1].axhline(0,color="#777777",linestyle="--",linewidth=1)
axes[1].set_ylabel("Incremental held-out ROC AUC")
fig.suptitle("Constant-temperature motor-state decoding from published source traces",fontsize=11)
fig.savefig(OUT/"M2_AIY_STATE_CONDITIONAL_ENCODING_V1.svg")
fig.savefig(OUT/"M2_AIY_STATE_CONDITIONAL_ENCODING_V1.png",dpi=220)

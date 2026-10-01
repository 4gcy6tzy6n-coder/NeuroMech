#!/usr/bin/env python3
"""Plot the preselected M2 discrete-state primary contrast and controls."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from audit_panel_alignment import require_matplotlib_panel_alignment

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial','DejaVu Sans','Liberation Sans']
plt.rcParams['svg.fonttype'] = 'none'  # svg.fonttype='none' keeps text editable.
plt.rcParams.update({'pdf.fonttype':42,'font.size':7,'axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':.8,'legend.frameon':False})

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_DATA=ROOT/'data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/canonical/seed_summary.csv'
DEFAULT_OUT=ROOT/'data/results/M2_DISCRETE_MOTOR_STATE_TRANSFER_V1/figures'
COMPS=(('Previous command sign','ACTION_STATE'),('Zero input','ZERO_STATE'),('Recipient-yoked state','YOKED_STATE'),('Fixed reactive policy','REACTIVE'))
BOOT=20_000;BOOT_SEED=8_765_501  # RNG is only for seed-block bootstrap resampling, not simulated observations.

def load(path):
 with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,default=DEFAULT_DATA);ap.add_argument('--output-dir',type=Path,default=DEFAULT_OUT);a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 rows=load(a.data);blocks=sorted({int(r['seed_block']) for r in rows});assert len(blocks)==32
 primary=[]
 for label,arm in COMPS:
  diffs=[]
  for b in blocks:
   x=float(next(r['tracking_mse'] for r in rows if int(r['seed_block'])==b and r['profile']=='LONG_BURST' and r['arm']=='SELF_STATE'))
   y=float(next(r['tracking_mse'] for r in rows if int(r['seed_block'])==b and r['profile']=='LONG_BURST' and r['arm']==arm))
   diffs.append(x-y)
  d=np.asarray(diffs);rng=np.random.default_rng(BOOT_SEED);draw=d[rng.integers(0,len(d),(BOOT,len(d)))].mean(axis=1)
  primary.append({'label':label,'arm':arm,'estimate':float(d.mean()),'low':float(np.quantile(draw,.025)),'high':float(np.quantile(draw,.975)),'n':len(d)})
 (a.output_dir/'figure_source_data.json').write_text(json.dumps({'metric':'tracking_mse','profile':'LONG_BURST','contrast':'SELF_STATE minus comparator; negative favors SELF_STATE','unit':'training seed block','interval':'percentile 95% bootstrap over seed blocks','bootstrap_draws':BOOT,'bootstrap_seed':BOOT_SEED,'contrasts':primary},indent=2)+'\n')
 y=np.arange(len(primary))[::-1];fig,ax=plt.subplots(figsize=(7.09,2.91),layout='constrained')  # 180 × 74 mm
 for yi,item in zip(y,primary):
  color='#484878' if item['arm']=='ACTION_STATE' else '#7884B4'
  ax.errorbar(item['estimate'],yi,xerr=[[item['estimate']-item['low']],[item['high']-item['estimate']]],fmt='o',ms=4.2 if item['arm']=='ACTION_STATE' else 3.6,color=color,mec='white',mew=.45,lw=1.8 if item['arm']=='ACTION_STATE' else 1.3,capsize=2.0,zorder=3)
 ax.axvline(0,color='#606060',lw=.8,ls=(0,(2,2)),zorder=1)
 ax.set_yticks(y,[x['label'] for x in primary]);ax.set_xlim(-.08,.025);ax.set_xlabel('Tracking MSE difference (SELF_STATE − comparator; n = 32 seed blocks, 95% bootstrap CI)')
 ax.set_title('Realized movement state improves on command sign, not clearly on state ablations',loc='left',fontsize=8,fontweight='bold',pad=8)
 ax.grid(axis='x',color='#e5e5e5',lw=.55);ax.set_axisbelow(True);ax.tick_params(axis='both',length=2.5,width=.7,pad=3)
 fig.align_ylabels();base=a.output_dir/'M2_DISCRETE_MOTOR_STATE_TRANSFER_V1'
 require_matplotlib_panel_alignment(fig,json_out=f'{base}.alignment.json',overlay_svg=f'{base}.alignment.svg',tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
 fig.savefig(f'{base}.svg',bbox_inches='tight');fig.savefig(f'{base}.pdf',bbox_inches='tight');fig.savefig(f'{base}.tiff',dpi=600,bbox_inches='tight');plt.close(fig)
 print(json.dumps({'status':'COMPLETE','source_rows':len(rows),'figure_source_data':str(a.output_dir/'figure_source_data.json'),'contrasts':primary},indent=2))
if __name__=='__main__':main()

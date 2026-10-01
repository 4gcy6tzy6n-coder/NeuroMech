#!/usr/bin/env python3
"""Supervised hidden-state estimation under action-coupled sensory dynamics."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_ACTION_CONDITIONED_STATE_ESTIMATION_V1"
CONTRACT = ROOT / "summery" / EXP / "CONTRACT.md"
SEEDS = tuple(range(930000, 930032))
LTC_ARMS = ("LTC_SENSORY_SITE", "LTC_OUTPUT_SITE", "LTC_NO_FEEDBACK", "LTC_DENSE_FEEDBACK", "LTC_SENSORY_YOKED")
GRU_ARMS = ("GRU_2", "GRU_4")
LEARNED = (*LTC_ARMS, *GRU_ARMS)
ARMS = (*LEARNED, "SIGNED_STATE_ORACLE")
COUPLINGS = (1.0, 0.0, -1.0)
T, NTRAIN, NTEST, BATCH, UPDATES, LR = 128, 256, 256, 32, 160, 0.003
NBOOT, BOOT_SEED, HIDDEN, SENSORY_UNITS, ODE_UNFOLDS = 20_000, 20261004, 4, 2, 4
OBS_Q, FLIP_HAZARD = 0.25, 1/40

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def make_data(seed: int, n: int, coupling: float, steps: int = T):
    rs = [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(7)]
    d0r, gr, flipr, ar, noise_r, vis_r, vinit_r = rs
    d0 = d0r.uniform(-1.5, 1.5, n).astype(np.float32)
    g = np.empty((n, steps), np.float32)
    g[:, 0] = gr.choice(np.array([-1., 1.], np.float32), n)
    flips = flipr.random((n, steps)) < FLIP_HAZARD
    for t in range(1, steps): g[:, t] = np.where(flips[:, t], -g[:, t-1], g[:, t-1])
    u = np.zeros((n, steps), np.float32)
    innovation = ar.normal(0, 0.22, (n, steps)).astype(np.float32)
    for t in range(steps): u[:, t] = np.clip((0.65*u[:, t-1] if t else 0) + innovation[:, t], -0.55, 0.55)
    d = np.empty((n, steps), np.float32); d[:, 0] = d0
    for t in range(1, steps): d[:, t] = np.clip(d[:, t-1] + coupling*u[:, t-1], -2., 2.)
    noise = noise_r.normal(0, .15, (n, steps)).astype(np.float32)
    y = g*d + noise
    visible = np.empty((n, steps), np.float32)
    visible[:, 0] = vinit_r.integers(0, 2, n)
    vf = vis_r.random((n, steps)) < OBS_Q
    for t in range(1, steps): visible[:, t] = np.where(vf[:, t], 1-visible[:, t-1], visible[:, t-1])
    u_prev = np.zeros_like(u); u_prev[:, 1:] = u[:, :-1]
    return {"displacement": d, "gradient": g, "observation": y*visible,
            "visible": visible, "motor_prev": u_prev, "coupling": np.full(n, coupling, np.float32)}

def tensors(data, indices=None):
    out={}
    for k,v in data.items():
        if indices is not None: v=v[indices]
        out[k]=torch.as_tensor(v,dtype=torch.float32)
    return out

class LTC(torch.nn.Module):
    def __init__(self, arm):
        super().__init__(); self.arm=arm
        self.w_rec=torch.nn.Parameter(torch.eye(HIDDEN)*.1+torch.randn(HIDDEN,HIDDEN)*.03)
        self.w_obs=torch.nn.Parameter(torch.randn(HIDDEN)*.3)
        self.w_vis=torch.nn.Parameter(torch.randn(HIDDEN)*.12)
        self.bias=torch.nn.Parameter(torch.full((HIDDEN,),-.6))
        self.raw_tau=torch.nn.Parameter(torch.full((HIDDEN,),.35))
        self.reversal=torch.nn.Parameter(torch.randn(HIDDEN)*.2)
        self.readout=torch.nn.Parameter(torch.randn(HIDDEN)*.2)
        self.readout_bias=torch.nn.Parameter(torch.zeros(()))
        self.beta=torch.nn.Parameter(torch.tensor(.25))
        mask=torch.zeros(HIDDEN)
        if arm in ("LTC_SENSORY_SITE","LTC_SENSORY_YOKED"): mask[:SENSORY_UNITS]=1
        if arm=="LTC_DENSE_FEEDBACK": mask[:]=1
        self.register_buffer("sensory_mask",mask)
    def initial(self,n): return torch.zeros(n,HIDDEN)
    def step(self,y,vis,h,motor,motor_yoked=None):
        u=motor if motor_yoked is None else motor_yoked
        dt=1/ODE_UNFOLDS; tau=F.softplus(self.raw_tau)+.1; leak=1/tau
        for _ in range(ODE_UNFOLDS):
            cur=F.linear(h,self.w_rec)+y[:,None]*self.w_obs+vis[:,None]*self.w_vis+self.bias
            if self.arm in ("LTC_SENSORY_SITE","LTC_DENSE_FEEDBACK","LTC_SENSORY_YOKED"):
                cur=cur+self.beta*u[:,None]*self.sensory_mask
            c=F.softplus(cur)
            h=(h+dt*c*self.reversal)/(1+dt*(leak+c))
        pred=F.linear(h,self.readout[None,:],self.readout_bias[None]).squeeze(-1)
        if self.arm=="LTC_OUTPUT_SITE": pred=pred+self.beta*motor
        return h,pred

class GRU(torch.nn.Module):
    def __init__(self,h):
        super().__init__(); self.h=h; self.cell=torch.nn.GRUCell(3,h); self.out=torch.nn.Linear(h,1)
    def initial(self,n): return torch.zeros(n,self.h)
    def step(self,y,vis,h,motor):
        h=self.cell(torch.stack([y,vis,motor],-1),h)
        return h,self.out(h).squeeze(-1)

def build(arm):
    if arm in LTC_ARMS:return LTC(arm)
    if arm=="GRU_2":return GRU(2)
    if arm=="GRU_4":return GRU(4)
    raise ValueError(arm)

def predict(data,model,arm,training=False):
    y,vis,u=data["observation"],data["visible"],data["motor_prev"]
    d=data["displacement"]; n,t=d.shape
    if arm=="SIGNED_STATE_ORACLE":
        est=torch.zeros(n); ps=[]
        for k in range(t):
            if k>0: est=torch.clamp(est+data["coupling"]*u[:,k],-2,2)
            est=torch.where(vis[:,k]>0, y[:,k]*data["gradient"][:,k], est)
            ps.append(est)
        pred=torch.stack(ps,1)
    else:
        h=model.initial(n); ps=[]
        for k in range(t):
            yoked=torch.roll(u[:,k],1) if arm=="LTC_SENSORY_YOKED" else None
            if arm in LTC_ARMS: h,p=model.step(y[:,k],vis[:,k],h,u[:,k],yoked)
            else: h,p=model.step(y[:,k],vis[:,k],h,u[:,k])
            ps.append(p)
        pred=torch.stack(ps,1)
    target=d
    if training:return (pred-target).square().mean()
    return pred.detach().numpy()

def write_csv(path,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)

def episode_rows(data,pred,seed,arm,coupling):
    d=data["displacement"]; e=pred-d
    return [{"training_seed":seed,"arm":arm,"coupling":coupling,"episode_id":i,
             "displacement_mse":float(np.mean(e[i]**2)),"displacement_mae":float(np.mean(np.abs(e[i]))),
             "prediction_bias":float(np.mean(e[i]))}
            for i in range(len(d))]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);ap.add_argument('--preflight',action='store_true');a=ap.parse_args()
    out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True);torch.set_num_threads(1)
    if a.preflight:
        if any(out.iterdir()):raise FileExistsError('preflight requires empty output directory')
        data=tensors(make_data(9301,8,1.,steps=16)); checks=[]
        for i,arm in enumerate(LEARNED):
            torch.manual_seed(300+i);m=build(arm);loss=predict(data,m,arm,True);loss.backward()
            dormant=[n for n,p in m.named_parameters() if p.grad is None]
            checks.append({"arm":arm,"trainable_parameters":sum(p.numel() for p in m.parameters()),
                           "finite_loss":bool(torch.isfinite(loss)),"finite_gradients":all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in m.parameters()),
                           "dormant_parameters":dormant})
        (out/'PREFLIGHT.json').write_text(json.dumps({"experiment_id":EXP,"outcomes_computed":False,
            "contract_sha256":sha(CONTRACT),"runner_sha256":sha(Path(__file__)),"python":platform.python_version(),
            "numpy":np.__version__,"torch":torch.__version__,"training":{"seed_first":SEEDS[0],"seed_last":SEEDS[-1],
            "episodes":NTRAIN,"steps":T,"updates":UPDATES,"batch":BATCH,"lr":LR},"checks":checks},indent=2)+'\n')
        print(json.dumps(checks,indent=2));return
    pre=out/'PREFLIGHT.json'
    if not pre.is_file():raise FileNotFoundError('run --preflight first')
    predata=json.loads(pre.read_text())
    if predata['contract_sha256']!=sha(CONTRACT) or predata['runner_sha256']!=sha(Path(__file__)):raise RuntimeError('contract/runner changed after preflight')
    if any((out/n).exists() for n in ('episode_results.csv','training_results.csv','RUN_METADATA.json')):raise FileExistsError('will not overwrite outcomes')
    episodes=[];fits=[];started=time.perf_counter()
    for si,seed in enumerate(SEEDS):
        train=tensors(make_data(seed*31+400,NTRAIN,1.))
        sample=np.random.default_rng(seed+880000).integers(0,NTRAIN,(UPDATES,BATCH))
        for ai,arm in enumerate(LEARNED):
            torch.manual_seed(seed*13+ai);model=build(arm);opt=torch.optim.Adam(model.parameters(),lr=LR);losses=[];ts=time.perf_counter()
            for step in range(UPDATES):
                ix=sample[step];batch={k:v[ix] for k,v in train.items()}
                loss=predict(batch,model,arm,True);opt.zero_grad(set_to_none=True);loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(),2.);opt.step();losses.append(float(loss.detach()))
            fits.append({"training_seed":seed,"arm":arm,"parameter_count":sum(p.numel() for p in model.parameters()),
                "updates":UPDATES,"training_seconds":time.perf_counter()-ts,"initial_loss":losses[0],
                "final_10_update_loss":float(np.mean(losses[-10:]))})
            for ci,c in enumerate(COUPLINGS):
                raw=make_data(11_000_000+si*20+ci,NTEST,c);td=tensors(raw)
                with torch.no_grad(): pred=predict(td,model,arm)
                episodes.extend(episode_rows(raw,pred,seed,arm,c))
        for ci,c in enumerate(COUPLINGS):
            raw=make_data(11_000_000+si*20+ci,NTEST,c);td=tensors(raw)
            pred=predict(td,None,'SIGNED_STATE_ORACLE')
            episodes.extend(episode_rows(raw,pred,seed,'SIGNED_STATE_ORACLE',c))
        print(f'completed seed block {seed} ({si+1}/{len(SEEDS)})',flush=True)
    write_csv(out/'episode_results.csv',episodes);write_csv(out/'training_results.csv',fits)
    (out/'RUN_METADATA.json').write_text(json.dumps({"experiment_id":EXP,"contract_sha256":sha(CONTRACT),
        "runner_sha256":sha(Path(__file__)),"runtime_seconds":time.perf_counter()-started,"episode_rows":len(episodes),
        "fit_rows":len(fits),"seeds":SEEDS,"couplings":COUPLINGS},indent=2)+'\n')
    print(f'wrote {len(episodes)} episode rows and {len(fits)} model fits to {out}')

if __name__=='__main__':main()

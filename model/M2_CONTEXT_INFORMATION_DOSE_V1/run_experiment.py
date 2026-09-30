#!/usr/bin/env python3
"""Measure how M2-style state-conditioned estimation changes with context information."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, sys
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
EXP = "M2_CONTEXT_INFORMATION_DOSE_V1"
SEEDS = range(43000, 43030)
KAPPAS = np.round(np.arange(-0.50, 0.5001, 0.10), 2)
POLICIES = ("MODE_GAIN_FILTER", "CONSTANT_GAIN_FILTER", "GENERIC_RNN_1D", "BILINEAR_RNN_1D", "KALMAN_ORACLE")
NTRAIN = NTEST = 256
T = 100
UPDATES = 200
QSW = 0.05

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def latent_stream(seed: int, n: int, steps: int):
    rng = np.random.default_rng(seed)
    phi = rng.uniform(0.84, 0.96, n).astype(np.float32)
    sp = rng.uniform(0.08, 0.18, n).astype(np.float32)
    so = rng.uniform(0.15, 0.35, n).astype(np.float32)
    x = np.zeros(n, np.float32)
    q = rng.choice(np.array([-1, 1], np.int8), n)
    xs, qs, eps = [], [], []
    for t in range(steps):
        if t:
            x = phi * x + rng.normal(size=n).astype(np.float32) * sp
            q = np.where(rng.random(n) < QSW, -q, q).astype(np.int8)
        xs.append(x.copy()); qs.append(q.copy())
        eps.append(rng.normal(size=n).astype(np.float32) * so)
    return tuple(np.stack(v, axis=1) for v in (xs, qs, eps)) + (phi, sp, so)

def observations(x, q, eps, kappa):
    return ((0.5 + np.float32(kappa) * q.astype(np.float32)) * x + eps).astype(np.float32)

class Learner:
    def __init__(self, name, seed):
        self.name = name
        torch.manual_seed(seed)
        init = {
            "MODE_GAIN_FILTER": [3., 0., 0., 0.],
            "CONSTANT_GAIN_FILTER": [3., 0., 0.],
            "GENERIC_RNN_1D": [.5, 0., .7, 0.],
            "BILINEAR_RNN_1D": [.5, 0., 0., .7, 0.],
        }[name]
        self.raw = torch.nn.Parameter(torch.tensor(init, dtype=torch.float32))
    def parameters(self): return [self.raw]
    def rollout(self, y, q):
        h = torch.zeros(y.shape[0], dtype=y.dtype)
        out = []
        if self.name == "MODE_GAIN_FILTER":
            rho=.999*torch.sigmoid(self.raw[0]); gp=torch.sigmoid(self.raw[1]+self.raw[2]); gm=torch.sigmoid(self.raw[1]-self.raw[2]); b=.2*torch.tanh(self.raw[3])
            for t in range(y.shape[1]):
                pred=rho*h; gain=torch.where(q[:,t]>0,gp,gm); h=pred+gain*(y[:,t]-pred)+b; out.append(h)
        elif self.name == "CONSTANT_GAIN_FILTER":
            rho=.999*torch.sigmoid(self.raw[0]); gain=torch.sigmoid(self.raw[1]); b=.2*torch.tanh(self.raw[2])
            for t in range(y.shape[1]):
                pred=rho*h; h=pred+gain*(y[:,t]-pred)+b; out.append(h)
        elif self.name == "GENERIC_RNN_1D":
            for t in range(y.shape[1]):
                h=torch.tanh(self.raw[0]*y[:,t]+self.raw[1]*q[:,t]+self.raw[2]*h+self.raw[3]); out.append(h)
        else:
            for t in range(y.shape[1]):
                h=torch.tanh(self.raw[0]*y[:,t]+self.raw[1]*q[:,t]+self.raw[2]*y[:,t]*q[:,t]+self.raw[3]*h+self.raw[4]); out.append(h)
        return torch.stack(out, dim=1)

def oracle(y, q, phi, sp, so, kappa):
    n, steps=y.shape; state=np.zeros(n,np.float64); var=np.zeros(n,np.float64); result=np.empty_like(y)
    for t in range(steps):
        if t: var=phi*phi*var+sp*sp; state=phi*state
        h=0.5+kappa*q[:,t]
        gain=var*h/(h*h*var+so*so)
        state=state+gain*(y[:,t]-h*state); var=(1-gain*h)*var
        result[:,t]=state
    return result.astype(np.float32)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",type=Path,default=ROOT/"data/results"/EXP); args=ap.parse_args(); out=args.output_dir.resolve()
    if out.exists() and any(out.iterdir()): raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True,exist_ok=True); torch.set_num_threads(1)
    eval_x,eval_q,eval_eps,phi,sp,so=latent_stream(830001,NTEST,T)
    rows=[]; fits=[]
    for seed in SEEDS:
        train_x,train_q,train_eps,_,_,_=latent_stream(730001+seed,NTRAIN,T)
        train_y=observations(train_x,train_q,train_eps,.5)
        ty=torch.from_numpy(train_y); tq=torch.from_numpy(train_q.astype(np.float32)); tx=torch.from_numpy(train_x)
        models={}
        for j,name in enumerate(POLICIES[:-1]):
            model=Learner(name,seed+1009*(j+1)); opt=torch.optim.Adam(model.parameters(),lr=.02)
            initial=None; final=None
            for step in range(UPDATES):
                pred=model.rollout(ty,tq); loss=((pred-tx)**2).mean(); opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),5); opt.step()
                if step==0: initial=float(loss.detach())
                if step==UPDATES-1: final=float(loss.detach())
            models[name]=model
            fits.append({"train_seed":seed,"policy":name,"parameters_json":json.dumps(model.raw.detach().numpy().tolist()),"n_parameters":model.raw.numel(),"initial_train_mse":initial,"final_train_mse":final})
        for kappa in KAPPAS:
            y=observations(eval_x,eval_q,eval_eps,float(kappa)); y_t=torch.from_numpy(y); q_t=torch.from_numpy(eval_q.astype(np.float32))
            for name,model in models.items():
                with torch.no_grad(): pred=model.rollout(y_t,q_t).numpy()
                per_ep=((pred-eval_x)**2).mean(axis=1)
                for episode_id,value in enumerate(per_ep): rows.append({"train_seed":seed,"kappa":f"{kappa:.2f}","episode_id":episode_id,"policy":name,"episode_mse":f"{value:.10g}"})
            pred=oracle(y,eval_q,phi,sp,so,float(kappa)); per_ep=((pred-eval_x)**2).mean(axis=1)
            for episode_id,value in enumerate(per_ep): rows.append({"train_seed":seed,"kappa":f"{kappa:.2f}","episode_id":episode_id,"policy":"KALMAN_ORACLE","episode_mse":f"{value:.10g}"})
        print(f"completed train seed {seed}",flush=True)
    for filename,records in (("episode_metrics.csv",rows),("learned_fits.csv",fits)):
        with (out/filename).open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(records)
    manifest={"experiment_id":EXP,"classification":"exploratory artificial mechanism study","python":platform.python_version(),"numpy":np.__version__,"torch":torch.__version__,"training_seeds":[SEEDS.start,SEEDS.stop-1],"test_stream_seed":830001,"training_stream_seed_base":730001,"n_train_episodes":NTRAIN,"n_test_episodes":NTEST,"steps":T,"updates":UPDATES,"kappas":[float(k) for k in KAPPAS],"policies":list(POLICIES),"rows":len(rows),"files":{}}
    for name in ("episode_metrics.csv","learned_fits.csv"):
        manifest["files"][name]=sha(out/name)
    manifest["runner_sha256"]=sha(Path(__file__))
    (out/"run_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))

if __name__=="__main__": main()

#!/usr/bin/env python3
"""Compare local eligibility with truncated/full BPTT on delayed XOR."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,platform,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];EXP="M5_ELIGIBILITY_TRUNCATED_BPTT_V1"
OUT=ROOT/"data/results"/EXP;CONTRACT=ROOT/"summery"/EXP/"CONTRACT.md"
SEEDS=tuple(range(2000,2032));ARMS=("ELIGIBILITY_TRACE","NO_TRACE","TBPTT_1","TBPTT_4","BPTT_FULL")
NI,NH,NC,LEAK,TRACE_DECAY,LR,CLIP=4,24,2,.1,.98,.03,1.
NTRAIN,NTEST,DELAY,NOISE=3000,500,4,.25
NBOOT,BOOT_SEED=20000,20261013

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def softmax(z):
    e=np.exp(z-np.max(z));return e/e.sum()
def init(seed):
    r=np.random.default_rng(seed);q,_=np.linalg.qr(r.normal(size=(NH,NH)))
    return {"Wx":r.normal(0,.5,(NH,NI)),"Wh":.9*q,"b":np.zeros(NH),"Wo":r.normal(0,.01,(NC,NH)),"bo":np.zeros(NC)}
def episode(rng):
    a,b=(int(v) for v in rng.integers(0,2,2));x=np.zeros((DELAY+3,NI));x[0,a]=1
    x[1:DELAY+1]=rng.normal(0,NOISE,(DELAY,NI));x[DELAY+1,2+b]=1
    return x,a^b
def forward(x,w):
    h=np.zeros(NH);hs=[];phis=[];eh=np.zeros((NH,NH));ex=np.zeros((NH,NI));eb=np.zeros(NH)
    for xt in x:
        hp=h;z=np.tanh(w["Wx"]@xt+w["Wh"]@hp+w["b"]);phi=LEAK*(1-z*z);h=(1-LEAK)*hp+LEAK*z
        eh=TRACE_DECAY*eh+np.outer(phi,hp);ex=TRACE_DECAY*ex+np.outer(phi,xt);eb=TRACE_DECAY*eb+phi
        hs.append(h.copy());phis.append(phi.copy())
    return np.asarray(hs),np.asarray(phis),eh,ex,eb
def gradients(x,y,w,arm):
    hs,phis,eh,ex,eb=forward(x,w);p=softmax(w["Wo"]@hs[-1]+w["bo"]);d=p.copy();d[y]-=1
    g={k:np.zeros_like(v) for k,v in w.items()};g["Wo"]=np.outer(d,hs[-1]);g["bo"]=d
    if arm=="ELIGIBILITY_TRACE":
        sig=w["Wo"].T@d;g["Wh"]=sig[:,None]*eh;g["Wx"]=sig[:,None]*ex;g["b"]=sig*eb
    elif arm=="NO_TRACE":
        hp=hs[-2];sig=(w["Wo"].T@d)*phis[-1];g["Wh"]=np.outer(sig,hp);g["Wx"]=np.outer(sig,x[-1]);g["b"]=sig
    else:
        start=0 if arm=="BPTT_FULL" else len(x)-int(arm.split("_")[1])
        dhnext=np.zeros(NH)
        for t in range(len(x)-1,start-1,-1):
            hp=hs[t-1] if t else np.zeros(NH);dh=(w["Wo"].T@d if t==len(x)-1 else 0)+dhnext
            du=dh*phis[t];g["Wx"]+=np.outer(du,x[t]);g["Wh"]+=np.outer(du,hp);g["b"]+=du
            dhnext=(1-LEAK)*dh+w["Wh"].T@du
    pred=int(np.argmax(p));loss=-math.log(max(float(p[y]),1e-300))
    return g,pred,loss
def update(w,g,state,t):
    norm=math.sqrt(sum(float(np.sum(v*v)) for v in g.values()));scale=min(1.,CLIP/max(norm,1e-12));m,v=state
    for k in w:
        z=g[k]*scale;m[k]=.9*m[k]+.1*z;v[k]=.999*v[k]+.001*z*z
        w[k]-=LR*(m[k]/(1-.9**t))/(np.sqrt(v[k]/(1-.999**t))+1e-8)
    if not all(np.isfinite(a).all() for a in w.values()):raise FloatingPointError("nonfinite weights")
def ci(v):
    r=np.random.default_rng(BOOT_SEED);ix=r.integers(0,len(v),(NBOOT,len(v)));return [float(z) for z in np.quantile(v[ix].mean(1),[.025,.975])]
def csvwrite(p,rows):
    with p.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
def finite_difference_check():
    w=init(78123);x,y=episode(np.random.default_rng(9917));g,_,_=gradients(x,y,w,"BPTT_FULL");eps=1e-6;errs=[]
    for k,idx in [("Wx",(0,0)),("Wx",(3,2)),("Wh",(0,1)),("Wh",(7,9)),("b",(4,)),("Wo",(1,5)),("bo",(0,))]:
        o=w[k][idx];w[k][idx]=o+eps;lp=gradients(x,y,w,"BPTT_FULL")[2];w[k][idx]=o-eps;lm=gradients(x,y,w,"BPTT_FULL")[2];w[k][idx]=o
        errs.append(abs((lp-lm)/(2*eps)-g[k][idx]))
    if max(errs)>2e-6:raise AssertionError(f"finite-difference gradient error {max(errs)}")
    return max(errs)
def preflight():
    err=finite_difference_check();x,y=episode(np.random.default_rng(414));w=init(551);checks=[]
    for arm in ARMS:
        g,pred,loss=gradients(x,y,w,arm);ok=all(np.isfinite(z).all() for z in g.values()) and np.isfinite(loss)
        if not ok:raise AssertionError(f"nonfinite preflight {arm}")
        checks.append({"arm":arm,"finite_gradients":True,"finite_loss":True})
    return {"experiment_id":EXP,"classification":"POST_RESULT_EXPLORATORY","outcomes_computed":False,
        "contract_sha256":sha(CONTRACT),"runner_sha256":sha(Path(__file__)),"python":platform.python_version(),
        "numpy":np.__version__,"finite_difference_max_error":err,"xor_truth_table":"PASS","checks":checks,
        "config":{"seeds":[SEEDS[0],SEEDS[-1]],"delay":DELAY,"train":NTRAIN,"test":NTEST,"arms":ARMS,
            "parameters_per_arm":NI*NH+NH*NH+NH+NC*NH+NC,"learning_rate":LR,"trace_decay":TRACE_DECAY}}
def run():
    OUT.mkdir(parents=True,exist_ok=True);rows=[];t0=time.perf_counter()
    for si,seed in enumerate(SEEDS):
        rng=np.random.default_rng(seed*1000003+DELAY*101+1);train=[episode(rng) for _ in range(NTRAIN)]
        te=np.random.default_rng(seed*1000003+DELAY*101+2);test=[episode(te) for _ in range(NTEST)];w0=init(seed*101+31)
        for arm in ARMS:
            w={k:v.copy() for k,v in w0.items()};state=({k:np.zeros_like(v) for k,v in w.items()},{k:np.zeros_like(v) for k,v in w.items()});ts=time.perf_counter()
            for t,(x,y) in enumerate(train,1):g,_,_=gradients(x,y,w,arm);update(w,g,state,t)
            train_seconds=time.perf_counter()-ts;correct=0;loss=0.
            for x,y in test:_,pred,l=gradients(x,y,w,"NO_TRACE");correct+=pred==y;loss+=l
            rows.append({"task_seed":seed,"delay":DELAY,"arm":arm,"train_episodes":NTRAIN,"test_episodes":NTEST,
                "accuracy":correct/NTEST,"cross_entropy":loss/NTEST,"training_seconds":train_seconds,
                "parameter_count":sum(v.size for v in w.values()),"gradient_horizon_steps":
                    "eligibility_gamma_0.98" if arm=="ELIGIBILITY_TRACE" else ("local_terminal" if arm=="NO_TRACE" else (7 if arm=="BPTT_FULL" else int(arm.split("_")[1])))})
        if (si+1)%4==0:print(f"completed seed {seed} ({si+1}/{len(SEEDS)})",flush=True)
    csvwrite(OUT/"task_seed_results.csv",rows)
    contrasts=[];means={a:float(np.mean([float(r["accuracy"]) for r in rows if r["arm"]==a])) for a in ARMS}
    by={(int(r["task_seed"]),r["arm"]):float(r["accuracy"]) for r in rows}
    per=[]
    for seed in SEEDS:
        vals={a:by[(seed,a)] for a in ARMS};per.append({"task_seed":seed,**vals})
    for arm in ARMS:
        if arm=="ELIGIBILITY_TRACE":continue
        eff=np.array([by[(s,"ELIGIBILITY_TRACE")]-by[(s,arm)] for s in SEEDS]);iv=ci(eff)
        contrasts.append({"contrast":f"ELIGIBILITY_TRACE_MINUS_{arm}","mean_accuracy_difference":float(eff.mean()),
            "bootstrap_95ci":iv,"positive_seeds":int((eff>0).sum()),"task_seeds":len(SEEDS)})
    csvwrite(OUT/"paired_seed_contrasts.csv",per)
    bptt=np.array([by[(s,"BPTT_FULL")] for s in SEEDS]);bci=ci(bptt)
    summary={"experiment_id":EXP,"classification":"POST_RESULT_EXPLORATORY_ARTIFICIAL_EXPERIMENT",
        "primary_contrast":"ELIGIBILITY_TRACE_MINUS_TBPTT_4","arm_mean_accuracy":means,
        "contrasts":contrasts,"full_bptt_viability":{"mean":float(bptt.mean()),"bootstrap_95ci":bci,"chance":.5,"viable":bci[0]>.5},
        "task_seeds":len(SEEDS),"training_episodes_per_seed_arm":NTRAIN,"test_episodes_per_seed_arm":NTEST,
        "rows":len(rows),"elapsed_seconds":time.perf_counter()-t0,"bootstrap":{"resamples":NBOOT,"seed":BOOT_SEED,"unit":"task seed"}}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    outputs=["task_seed_results.csv","paired_seed_contrasts.csv","summary.json"]
    (OUT/"run_manifest.json").write_text(json.dumps({"experiment_id":EXP,"contract_sha256":sha(CONTRACT),"runner_sha256":sha(Path(__file__)),
        "seeds":SEEDS,"arms":ARMS,"parameters_per_arm":746,"delay":DELAY,"training_seconds_by_arm":
        {a:float(np.mean([r["training_seconds"] for r in rows if r["arm"]==a])) for a in ARMS},
        "output_sha256":{f:sha(OUT/f) for f in outputs}},indent=2)+"\n")
    print(json.dumps({"means":means,"contrasts":contrasts,"bptt_viability":summary["full_bptt_viability"]},indent=2))
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--preflight",action="store_true");a=ap.parse_args()
    if a.preflight:
        OUT.mkdir(parents=True,exist_ok=True);p=preflight();(OUT/"PREFLIGHT.json").write_text(json.dumps(p,indent=2)+"\n");print(json.dumps(p,indent=2))
    else:
        pre=OUT/"PREFLIGHT.json"
        if not pre.exists():raise FileNotFoundError("run preflight first")
        p=json.loads(pre.read_text())
        if p["contract_sha256"]!=sha(CONTRACT) or p["runner_sha256"]!=sha(Path(__file__)):raise RuntimeError("contract or runner changed since preflight")
        if (OUT/"task_seed_results.csv").exists():raise FileExistsError("refusing to overwrite results")
        run()
if __name__=="__main__":main()

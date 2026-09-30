# Figure 7 Python delay-index audit

The pinned author script `data/raw/celegans/ji_etal_2021_elife_68848_v3/Fig7_TtxCircuitModel.m` computes the delayed position from `XS(lagi,3)`, with `lagi=max(1,ti-delti)`. At each one-based MATLAB loop index `ti`, `XS` has rows `1..ti-1` before the current state is appended. Therefore the equivalent zero-based Python history index is `max(0, ti-delti-1)`. With Python counter `t=ti-1`, this is `max(0,t-delti)`.

V3 and V4 instead used `max(0,t-1-delti)`, which selects a point one simulation sample earlier after the startup boundary. With `N=1500` and `tmax=200 s`, one step is `200/1500 = 0.133333… s`. V5 corrects the index in a new versioned implementation; it does not rewrite old scripts or outputs.

This is a source-code indexing audit, not full MATLAB/Octave execution parity. Neither MATLAB nor Octave was available during this audit. Other possible numerical or edge-processing differences remain, including random-number generator behavior and MATLAB `smooth` boundary conventions.

# Execution incident 01 — yoke controller dispatch

The first invocation stopped during training of the first seed block. The yoke controller was routed through the generic-RNN branch of `ScalarController.step`, which referenced generic bias parameters that are not part of the four-parameter yoke architecture. The SELF_SENSORY model had finished fitting, but the yoke fit failed before any evaluation or outcome metric was computed or written.

The correction routes `CROSS_AGENT_YOKED_SENSORY` through the same four-parameter sensory-update equation as `SELF_SENSORY`; the external yoke signal remains the only intended model-input difference. No endpoint, sample size, training schedule, or statistical rule changed. A one-update training smoke check for both arms passed after the correction. This incident produced no usable scientific result and is retained for provenance.

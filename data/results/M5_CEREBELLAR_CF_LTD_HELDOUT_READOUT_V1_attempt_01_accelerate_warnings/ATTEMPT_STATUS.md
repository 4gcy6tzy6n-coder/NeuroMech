# Attempt 01 status — noncanonical

The first complete execution emitted NumPy `RuntimeWarning` messages from matrix multiplication on this macOS host. Input values, saved outputs, and all session summaries were finite, but warning-producing outputs are not used as the canonical run. The runner now computes these small products with explicit contractions. The full rerun passed with `RuntimeWarning` promoted to errors and reproduced every group/method summary to a maximum absolute difference of `3.4e-16`.

This directory is retained for provenance only. The canonical results are in the sibling `M5_CEREBELLAR_CF_LTD_HELDOUT_READOUT_V1/` directory.

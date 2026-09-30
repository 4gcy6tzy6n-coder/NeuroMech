# GitHub experiment-round workflow

The publication remote for the new NeuroMotif repository is `neuromotif` (`https://github.com/4gcy6tzy6n-coder/NeuroMotif.git`). The existing `origin` points to a different repository and must not be used for NeuroMotif publication.

For each completed experiment round, publish one isolated commit to `main` before starting another round:

1. Put runnable model/benchmark code in `model/<round>/`.
2. Put generated result files in `data/results/<round>/` (source datasets stay in `data/raw/`).
3. Put protocol, scientific summary, strengths, failures, and corrections in `summery/<round>/` (`summery` is the owner's requested directory spelling).
4. Include checksums and enough provenance to connect code, protocol, and outputs. Keep public source data under `data/raw/` only when it is appropriately distributable; do not add large downloaded archives or credentials to a round commit.
5. Review the staged path list, commit only that round's files, and push to `neuromotif main` before starting the next round. Never stage the full working tree; this workspace contains unrelated and locally acquired research files.
6. After pushing, verify the remote commit with `git ls-remote neuromotif refs/heads/main` or a fetch and compare the commit ID.

The existing `experiments/` directories remain the detailed local execution records. The GitHub directories are the organized publication mirror. Never include unrelated working-tree changes in a round commit. Keep each completed round's negative, null, and corrected results; do not overwrite them with later experiments.

# M2 sequential binary-decision transfer V1 — failure and boundary log

The primary aligned task showed a useful terminal-accuracy gain over the context-free constant-gain ablation, but the gain reversed under mapping shift. The mode-gain accuracy dropped to 0.519 in REVERSED, close to chance, while the context-free filter reached 0.637. The state-conditioned operation is therefore not robust when its assumed context/evidence relationship is wrong.

The Bayes oracle reached 0.838 accuracy in ALIGNED and REVERSED and 0.760 in INDEPENDENT. The learned mechanism does not recover the task-aware posterior, leaving a substantial gap. The bilinear RNN's lower accuracy is not proof of biological specificity: it uses a different recurrence and its fit depends on the fixed optimizer and training budget.

This is a new task objective (static binary inference and terminal choice), but the context-dependent evidence availability is still an artificial assumption. Cross-task replication within this generator family is not independent biological evidence and does not verify that the worm circuit estimates sensor reliability. The outcome supports only a synthetic principle of conditional evidence integration with mismatch cost.

Do not raise the task's cue signal strength, change sequence length, or tune the update after seeing these results and report it as the same experiment. Any extension needs new seeds and a new contract. To advance beyond this task family, the next experiment should use a genuinely different input-generation mechanism or a second biological computation such as M1, rather than another parameter sweep of this binary-evidence toy problem.

# M5 eligibility trace on learnable delayed temporal XOR — failure log

## What failed in V1

M10 V1 used online SGD and the standard BPTT arm remained near binary chance at delays 4, 16, and 64. Its near-zero eligibility-minus-no-trace result was therefore inconclusive: the task was not shown learnable by the conventional gradient baseline. The V1 outputs remain unchanged and are not retrospectively reclassified as a mechanism failure.

## What the calibration found

Short-delay calibration found that Adam at `lr=0.03` made BPTT learn the delay-4 task reliably. The same training exposure did not make delays 16/64 reliably learnable; longer-delay runs were highly initialization-sensitive. V2 therefore froze delay 4 as its only primary task condition, used disjoint task seeds `1000..1029`, and did not claim a long-delay result.

## V2 limitation and next boundary

The local trace improves accuracy over the no-trace local update, but BPTT is nearly perfect and substantially better. The current result does not establish computational efficiency because wall-clock or operation-count budgets were not matched. It also uses one recurrent architecture, one task generator, one short delay, and one optimizer. Any follow-up must preserve the negative BPTT gap and test a principled resource constraint or a distinct task family; changing the trace decay or selecting a favorable delay after these outcomes would be post-result tuning and needs a new version.

## Scientific scope

This is a synthetic algorithm experiment. It does not measure animal learning, climbing-fiber activity, synaptic eligibility, or a neural implementation of this RNN update. It is not, by itself, an NMI-level contribution.

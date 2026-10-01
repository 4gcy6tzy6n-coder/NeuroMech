# M5 interval-retuning source-data schema inventory

**Purpose:** verify the actual downloaded MATLAB structure and its field semantics before analysis. This inventory reports field names, storage types, dimensions, and documented alignment only; it contains no biological outcome summaries.

## Acquisition identity

- Dataset: Wagner (2024), Dryad DOI `10.5061/dryad.bk3j9kdm6`, version 4.
- Files and matching Dryad/local SHA-256 values: [`ACQUISITION_MANIFEST.json`](../../data/raw/cerebellar_interval_timing_dryad_v4/ACQUISITION_MANIFEST.json).
- The MATLAB files are v7.3/HDF5 containers. MATLAB cell references are represented as HDF5 object references, and HDF5 array axis order is reversed relative to MATLAB's in-memory display.

## Observed container and record structure

- Root variable `groups`: MATLAB cell array represented in HDF5 as a `1 × 3` reference array.
- Each group cell references another cell array of session structures. The source analysis labels the groups `1-s expert`, `2-s novice / 1-s expert`, and `2-s expert`; these labels come from `learning_1s_to_2s_GrC_CF.m` in the [author's repository](https://github.com/wagnerlabnih/garcia-garcia-neuron-2024).
- Session records contain arrays with session-dependent neuron and movement dimensions. The original README describes each record as one mouse on one session. The inspected exemplar structs do not expose a separate stable trial ID or explicit mouse-ID field; group and within-group position are the source-code indexing convention. This is a schema observation, not a claim that no ID is available elsewhere in the paper's materials.

## Relevant fields and observed semantics

| Field | Observed representation | Meaning documented by source README/code |
|---|---|---|
| `midAlgn.sigFilt_GrC` | float32, HDF5 time × GrC × trial | z-scored filtered GrC activity, aligned to movement midpoint |
| `midAlgn.sp_CF` | uint8, HDF5 time × CF × trial | binary CF spike train aligned to movement midpoint |
| `midAlgn.sigFilt_CF` | float32, HDF5 time × CF × trial | z-scored filtered CF activity aligned to movement midpoint |
| `midAlgn.lick`, `midAlgn.pos`, `midAlgn.sol` | uint8 / float32 trial-aligned arrays | licking, handle position, and solenoid signals aligned to movement midpoint |
| `rewAlgn.*`, `startAlgn.*` | nested MATLAB structs | corresponding signals aligned to reward or movement start |
| `tmpxCb`, `dtimCb` | float64 time vector / scalar | imaging time base and sampling step |
| `tmpxx`, `dtb` | float64 time vector / scalar | behavioral/DAQ time base and sampling step |
| `rewarded`, `rewtimes`, `midpt`, `trueend`, `rewdel` | float64 trial vectors | reward flag and event/movement timestamps or delay values; the author script recomputes `rewdel` from timestamps in analysis sections |
| `goodmvdir`, `mvlen` | numeric trial vectors | movement-quality/direction filter and movement duration |
| `nIC_GrC`, `nIC_CF` | numeric scalars | cell counts for the session |

An inspected session instance had `midAlgn.sigFilt_GrC` with HDF5 shape `301 × 54 × 138` and `midAlgn.sp_CF` with shape `301 × 9 × 138`; dimensions vary by session. These are schema examples, not coverage or biological effect estimates.

## Analysis boundary

The source code's interval-retiming analysis uses movement-aligned GrC activity, reward/movement timestamps, CF spike trains, and the 1 s versus 2 s session grouping. The author model applies CF-dependent LTD to GrC activity in a preceding approximately 150 ms interval; it is a modeled synaptic rule, not a direct measurement of those synaptic weights. The next analysis will first reproduce source-defined timing summaries and retain the source's grouping/filters, then separately formulate any new AI transfer claim. The 1 s-to-2 s recordings are longitudinally grouped, but cell-level observations are nested in session/animal and must not be treated as independent replicates.

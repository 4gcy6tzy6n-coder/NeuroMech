# A cerebellar granule cell–climbing fiber computation to learn to track long time intervals

[https://doi.org/10.5061/dryad.bk3j9kdm6](https://doi.org/10.5061/dryad.bk3j9kdm6)

Data files (stored in matlab (.mat) format) are used to produce main and supplementary figures. The description of all variables is as follows:

For each mouse on each session, there is a data structure with many fields, some of which are present only contextually for some session types.

Call the current structure session’s data structure "curd"

"curd" contains many fields, among them:

•	nIC_GrC, nIC_CF - number of GrCs or CFs

•	pixh, pixw - image height and width in pixels

•	ICmat_CF, ICmat_GrC – Npixh X Npixw X Ngrc or Ncf

•	dtb, dtimCb, dtDLC - sampling time step in sec for NIdaq behavioral data, imaging data, and behavioral video data

•	ntb, ntimCb - total # of samples; NIdaq or microscope

•	nc - total number of detected forelimb movements

•	"midAlgn" and "rewAlgn." Each of these fields is in turn another structure

•	Several variables are acquired on the NIdaq and are of length ntb

```
 lick - binary lick sensor contacts

 frameCb - imaging frame counter

 pos - ntb X 2 matrix of x-y handle positions

 sol - binary solenoid gate
```

•	Several variables are based on the microscope acquisiton and have length ntimCb

```
 sigFilt_GrC, sigFilt_CF, spMat_CF - nIC_GrC X ntimCb or nIC_CF X ntimCb matrix of z-scored cell fluorescence or binary spike trains
```

•	goodmvdir - nc X 1 binary vector, 1 for movements that passed start/mid/end/reward alignment tests

•	rewtimes, truestart, midpt, trueend - detected times of reward, and movement start, middle, and end

•	valid_lick_trials, goodDLC - nc X 1 vector, 1 for trials where lick or camera data passed QC

•	tmpxx, tmpxCb, tmpxDLCnew - vector of time stamps centered on 0 sec with sample interval dtb, dtimCb, or dtDLC

curd.midAlgn/startAlgn/rewAlgn fields

•	sigFilt_GrC, sigFilt_CF, sp_CF - [nc X nIC X nt] matrix of GrC or CF zscored fluorescence or CF spikes, trials-by-cells-by-timepoints per trial, nt corrresponds to lengths of tmpxCb

```
Center of time axis is 0s wrt movement midpoint, start point, or reward time for midAlgn, startAlgn, rewAlgn respectively
```

•	sol - nc X nt matrix of binary solenoid openings

•	lick - same but for binary lick sensor contacts

•	pos Nmv X 2 X Nt_b same but for X and Y handle position

## Code/Software

Corresponding code to produce figures from these data can be found in [https://github.com/wagnerlabnih/garcia-garcia-neuron-2024](https://github.com/wagnerlabnih/garcia-garcia-neuron-2024)

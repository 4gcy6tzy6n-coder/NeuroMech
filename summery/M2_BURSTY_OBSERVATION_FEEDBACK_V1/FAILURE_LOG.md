# M2 bursty-observation feedback placement — failure lessons

1. **The strongest baseline remains unresolved.** Sensory-site feedback beat the output-site and four-parameter generic recurrent controls, but its paired contrast against the 8-unit GRU crossed zero. Do not report this as a general recurrent-learning advantage or as the full frozen mechanism-transfer criterion passing.
2. **Tracking and recovery tell different stories.** The sensory-site policy had lower average squared error and lower action energy, while output-site persistence reached the post-gap recovery criterion sooner. Do not turn the MSE result into a faster-recovery claim.
3. **The operating regime is synthetic.** Equal expected missingness with different Markov burst lengths is useful for probing the computation, but the mask process is not claimed to model worm thermotaxis or natural visual occlusion.
4. **Capacity and fit resources differ.** The structured and small generic policies each have four parameters; the GRU has 321. Equal episodes, optimizer updates, batch size, and sequence tokens do not imply equal compute or capacity.
5. **The result is post-result exploratory.** Previous M2 outcomes informed the new task and comparator set. It is not a prospective confirmatory test. No biological outcomes were used in this artificial study.

# Figure 7 model source

Primary source: Ji et al., “Corollary discharge promotes a sustained motor state in a neural circuit for navigation,” *eLife* 10:e68848 (2021), DOI `10.7554/eLife.68848`.

The Python model translation uses the official supplementary archive `elife-68848-fig7-data1.zip` and the extracted author script `Fig7_TtxCircuitModel.m`. The archive was downloaded from Europe PMC's article supplementary-files bundle for PMCID `PMC8139836` on 2026-09-30, then extracted without modification. SHA-256 values are recorded in `SHA256SUMS.txt`.

The source script is an author-provided Figure 7 computational model, not animal-level raw data. It includes a 50-agent thermotaxis simulation and MATLAB plotting/analysis code. The project runner ports the state update and navigation logic; it does not execute MATLAB, and its four-sample moving-average run segmentation may differ at edges from MATLAB `smooth` behavior.

Retrieval endpoint: `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8139836/supplementaryFiles`

Article: https://elifesciences.org/articles/68848v2

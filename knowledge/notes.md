# Literature Synthesis Notes

## Scope and Corpus Profile
- Total sources: 36
- Primary papers/reports: 35
- Recency (2023+): 16
- Focus: reactor antineutrino safeguards, spectral/flux modeling, statistical detection, and fusion-fission blanket pathways.

## Core Equation Families
- Isotope-mixture antineutrino spectrum: `S_tot(E_nu)=sum_i f_i S_i(E_nu)` links burnup/fuel evolution to spectral shifts (e.g., SRC records mapped to Mueller/Huber/Daya Bay lineage).
- Detection-rate forward model: `N_det ~ (N_p/(4*pi*L^2)) * integral epsilon(E) sigma_IBD(E) S(E,t) dE` ties detector assumptions to observability.
- Hypothesis testing/change detection statistics: likelihood-ratio style statistics for diversion/abnormal-operation detection.

## Agreement and Comparator Structure
- Agreement: safeguards papers consistently report that count-rate + spectral-shape information improves over count-only baselines when detector systematics are controlled.
- Agreement: spectrum-model papers agree that fissile isotopic fractions and conversion assumptions dominate prediction uncertainty.
- Comparator lineage: baseline no-diversion operations vs perturbed fuel-cycle/material cases, then detector-constrained inference.
- Contradiction boundary: anomaly-focused papers differ on root-cause decomposition (conversion model deficits vs reactor-data tensions), affecting priors for safeguards thresholds.

## Fusion-Adjacent Relevance
- Hybrid blanket/breeding studies provide parameter ranges and material-process pathways for fissile production potential, enabling scenario priors for diversion detectability studies.
- These sources are often conceptual/system-level and should be linked to uncertainty-aware simulation, not treated as plant-specific truth.

## Reusable Assumptions and Limitations
- Reusable assumptions: parameterized detector efficiency/background/resolution/standoff; open reactor power/burnup proxies; explicit fuel/blanket composition knobs.
- Reusable limitations: site background nonstationarity, calibration drift, nuclear data covariance, and limited open data for proprietary fusion plant designs.

## High-Value Derivation Inputs for Downstream Phases
- SRC entries with explicit equations should be used to define simulation forward model and statistical test statistics before novelty claims.
- Extraction completeness is partial/substantial for many recent papers due limited direct full-text retrieval in this pass; targeted PDF-level extraction recommended for theorem/proof-heavy claims.

## Source-to-Claim Linking Guidance
- Use `knowledge/source_index.json` for compact lookup of assumptions/equations/limitations.
- Use per-source `evidence_atoms` in `knowledge/refs.jsonl` for claim-evidence closure in later phases.

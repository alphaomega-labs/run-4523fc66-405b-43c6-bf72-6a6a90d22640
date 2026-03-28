# Extraction Plan

1. Core contribution selection
- Primary contribution extracted from EXP-ED-01 is nuisance-aware robust detector simulation + claim closure summaries + symbolic audit hooks.

2. Concrete source symbols located
- experiments/EXP-ED-01/src/exp_ed_01/simulation.py::run_simulation
- experiments/EXP-ED-01/src/exp_ed_01/analysis.py::summarize_claims
- experiments/EXP-ED-01/src/exp_ed_01/symbolic.py::run_sympy_audit

3. Source-to-public API mapping
- run_simulation -> antineutrino_safeguards.simulation.FusionSafeguardsSimulator
- summarize_claims -> antineutrino_safeguards.analysis.summarize_claims
- run_sympy_audit -> antineutrino_safeguards.symbolic.run_symbolic_audit

# antineutrino-safeguards

## Overview
`antineutrino-safeguards` packages reusable simulation and claim-analysis components extracted from the validated EXP-ED-01 contribution: robust minimax-style monitoring comparisons under nuisance shifts (background drift, standoff, energy resolution, and prior-family stress).

Core contribution exposed in this package:
- A deterministic scenario simulator for baseline vs robust detector comparison.
- Claim summary metrics aligned with DMM-C1, DMM-C2, and DMM-C3 evaluation framing.
- A lightweight symbolic consistency audit for monotonicity, likelihood-ratio identity, and stability bounds.

## Installation
Canonical omegaXiv user flow:
1. `pip install omegaxiv`
2. `ox install antineutrino-safeguards==0.1.0`

Maintainer/dev-only source install (not the canonical user path):
- `pip install -e packages/antineutrino-safeguards`

Additive MCP registration options:
- `ox install antineutrino-safeguards==0.1.0 --mcp`
- `ox install antineutrino-safeguards==0.1.0 --mcp=codex`
- `ox install antineutrino-safeguards==0.1.0 --mcp=claude`
- `ox install antineutrino-safeguards==0.1.0 --mcp=all`

## Configuration
The package uses a `MonitoringConfig` dataclass. You can use defaults or provide explicit sweeps.

```python
from antineutrino_safeguards import MonitoringConfig

config = MonitoringConfig(
    seeds=(101, 202),
    alpha_targets=(1e-3,),
    background_drift_slope=(0.0, 0.01, 0.02),
    energy_resolution_pct=(4.0, 6.0),
    prior_family_id=("huber_nominal", "conservative_shifted"),
    standoff_m=(25.0, 50.0),
)
```

## Usage Examples

```python
from antineutrino_safeguards import (
    FusionSafeguardsSimulator,
    MonitoringConfig,
    rank_monitoring_regimes,
    summarize_claims,
)

config = MonitoringConfig()
simulator = FusionSafeguardsSimulator(config)
records = simulator.run()
summary = summarize_claims(records)
rankings = rank_monitoring_regimes(records, top_k=3)

print(summary.dmm_c1_delay_win_rate)
print(rankings[0].score)
```

```python
from antineutrino_safeguards import run_symbolic_audit

checks = run_symbolic_audit()
print(checks["SYMPY-C1-2"])
```

## MCP Companion Interface
This package includes a stdio MCP companion server in `antineutrino_safeguards.mcp_server`.

What it exposes:
- `simulate_monitoring`: runs the simulator and returns sampled records.
- `summarize_claims`: computes DMM claim-summary metrics.
- `rank_regimes`: ranks regimes by delay/FAR/TPR composite score.
- `symbolic_audit`: returns symbolic consistency checks.

Launch (stdio transport):
- `python -m antineutrino_safeguards.mcp_server --serve`

One-shot tool invocation example:
- `python -m antineutrino_safeguards.mcp_server --tool summarize_claims --input '{"config": {"seeds": [1, 2]}}'`

How MCP maps to normal Python API:
- MCP tools call the same package functions used in import-based workflows (`FusionSafeguardsSimulator.run`, `summarize_claims`, `rank_monitoring_regimes`, `run_symbolic_audit`).

Example client config fragment:

```json
{
  "mcpServers": {
    "antineutrino-safeguards": {
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "antineutrino_safeguards.mcp_server", "--serve"]
    }
  }
}
```

## Troubleshooting
- If simulation outputs look empty, confirm at least one value is present for each sweep dimension in `MonitoringConfig`.
- If MCP returns `unknown tool`, call `tools/list` first or use one of the documented tool names.
- For deterministic comparisons, keep seed tuples fixed across runs.

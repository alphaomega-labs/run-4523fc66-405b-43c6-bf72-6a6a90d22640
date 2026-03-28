# EXP-ED-01 Validation Package

This experiment implements the `experiment_design` benchmark plan for claims `DMM-C1..DMM-C3`.

## Goal
Evaluate robust antineutrino monitoring performance under open, parameterized nuisance sweeps with matched-FAR comparators and symbolic theorem audits from `phase_outputs/SYMPY.md`.

## Layout
- `run_experiments.py`: CLI entrypoint for simulation, analysis, plotting, and SymPy checks.
- `configs/benchmark_config.json`: Seeds, baselines, sweeps, metrics, and acceptance criteria.
- `src/exp_ed_01/`: Reusable package code.
- `tests/`: Regression and symbolic smoke tests.
- `outputs/`: Generated data, summaries, and symbolic reports.

## Environment
Use `experiments/.venv` and install packages with:
- `uv pip install --python experiments/.venv/bin/python numpy pandas matplotlib seaborn sympy scipy pypdf pytest ruff mypy`

If `uv` is unavailable, fallback:
- `experiments/.venv/bin/python -m pip install numpy pandas matplotlib seaborn sympy scipy pypdf pytest ruff mypy`

## Run
From workspace root:
- `PYTHONPATH=experiments/EXP-ED-01/src experiments/.venv/bin/python experiments/EXP-ED-01/run_experiments.py`

## Outputs
- Figures: `paper/figures/exp_ed_01_far_delay_frontier.pdf`, `paper/figures/exp_ed_01_transfer_degradation.pdf`
- Tables: `paper/tables/exp_ed_01_calibration_by_prior.csv`, `paper/tables/exp_ed_01_delay_ratio_by_regime.csv`, `paper/tables/exp_ed_01_far_failure_partition_by_prior_standoff_drift.csv`
- Data: `paper/data/exp_ed_01_aggregated_metrics.csv`, plus run-level datasets in `experiments/EXP-ED-01/outputs/data/` including `far_failure_partition_by_prior_standoff_drift.csv`
- Symbolic reports: `experiments/EXP-ED-01/outputs/sympy/sympy_report.md`, `experiments/EXP-ED-01/outputs/sympy/theorem_checks.csv`

## Test
- `PYTHONPATH=experiments/EXP-ED-01/src experiments/.venv/bin/python -m pytest experiments/EXP-ED-01/tests -q`

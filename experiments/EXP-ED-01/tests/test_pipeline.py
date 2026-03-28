from pathlib import Path

from exp_ed_01.config import load_config
from exp_ed_01.simulation import PROPOSED_METHOD, run_simulation
from exp_ed_01.symbolic import run_sympy_audit


def test_simulation_has_expected_columns() -> None:
    cfg = load_config(Path('experiments/EXP-ED-01/configs/benchmark_config.json'))
    df = run_simulation(cfg)
    assert not df.empty
    assert PROPOSED_METHOD in set(df['baseline'])
    for col in ['FAR_at_target_alpha', 'MedianDetectionDelay_days', 'TPR_at_alpha_1e-3']:
        assert col in df.columns


def test_sympy_audit_runs(tmp_path: Path) -> None:
    report = tmp_path / 'report.md'
    table = tmp_path / 'checks.csv'
    results = run_sympy_audit(report, table)
    assert report.exists()
    assert table.exists()
    assert all(bool(v) for v in results.values())

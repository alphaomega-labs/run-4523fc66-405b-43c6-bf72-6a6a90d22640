from antineutrino_safeguards import (
    FusionSafeguardsSimulator,
    MonitoringConfig,
    rank_monitoring_regimes,
    run_symbolic_audit,
    summarize_claims,
)


def test_simulation_claim_summary_pipeline() -> None:
    config = MonitoringConfig(
        seeds=(11, 22),
        alpha_targets=(1e-3,),
        background_drift_slope=(0.0, 0.02),
        energy_resolution_pct=(4.0, 6.0),
        prior_family_id=("huber_nominal", "conservative_shifted"),
        standoff_m=(25.0, 75.0),
    )
    simulator = FusionSafeguardsSimulator(config)
    records = simulator.run()

    expected_count = (
        len(config.seeds)
        * len(config.alpha_targets)
        * len(config.background_drift_slope)
        * len(config.energy_resolution_pct)
        * len(config.prior_family_id)
        * len(config.standoff_m)
        * (1 + len(config.baselines))
    )
    assert len(records) == expected_count

    summary = summarize_claims(records)
    assert 0.0 <= summary.dmm_c1_delay_win_rate <= 1.0
    assert 0.0 <= summary.dmm_c1_calibration_violation_rate <= 1.0
    assert summary.dmm_c2_delay_ratio_median > 0.0
    assert summary.dmm_c3_transfer_degradation_ratio > 0.0


def test_rankings_and_symbolic_checks() -> None:
    simulator = FusionSafeguardsSimulator(MonitoringConfig(seeds=(1,), standoff_m=(25.0, 50.0)))
    rankings = rank_monitoring_regimes(simulator.run(), top_k=3)
    assert len(rankings) == 3
    assert rankings[0].score >= rankings[-1].score

    checks = run_symbolic_audit()
    assert set(checks.keys()) == {
        "SYMPY-C1-1",
        "SYMPY-C1-2",
        "DMM-T2-SC2.2",
        "DMM-T3-SC3.2",
    }
    assert all(checks.values())

from antineutrino_safeguards import (
    FusionSafeguardsSimulator,
    MonitoringConfig,
    rank_monitoring_regimes,
    summarize_claims,
)


def main() -> None:
    config = MonitoringConfig(seeds=(101, 202), standoff_m=(25.0, 50.0), energy_resolution_pct=(4.0, 6.0))
    simulator = FusionSafeguardsSimulator(config)
    records = simulator.run()

    summary = summarize_claims(records)
    top = rank_monitoring_regimes(records, top_k=3)

    print("DMM-C1 delay win rate:", round(summary.dmm_c1_delay_win_rate, 4))
    print("DMM-C1 calibration violation rate:", round(summary.dmm_c1_calibration_violation_rate, 4))
    print("Top regime score:", round(top[0].score, 4), "regime_id=", top[0].regime_id)


if __name__ == "__main__":
    main()

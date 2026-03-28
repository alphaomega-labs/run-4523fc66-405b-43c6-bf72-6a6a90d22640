from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .simulation import PROPOSED_METHOD


@dataclass(frozen=True)
class ClaimSummary:
    dmm_c1_delay_win_rate: float
    dmm_c1_calibration_violation_rate: float
    dmm_c1_far_inflation_p95: float
    dmm_c2_delay_ratio_median: float
    dmm_c2_far_residual_mean: float
    dmm_c3_transfer_degradation_ratio: float


def bootstrap_ci(
    series: pd.Series,
    num_bootstrap: int = 400,
    alpha: float = 0.05,
    seed: int = 123,
) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    values = series.to_numpy(dtype=float)
    if values.size == 0:
        return (float('nan'), float('nan'), float('nan'))
    samples = []
    for _ in range(num_bootstrap):
        sampled = rng.choice(values, size=values.size, replace=True)
        samples.append(float(np.median(sampled)))
    low = float(np.quantile(samples, alpha / 2.0))
    med = float(np.median(samples))
    high = float(np.quantile(samples, 1.0 - alpha / 2.0))
    return low, med, high


def summarize_claims(df: pd.DataFrame) -> ClaimSummary:
    proposed = df[df['baseline'] == PROPOSED_METHOD]
    bl1 = df[df['baseline'] == 'BL1 Single-prior likelihood-ratio detector']

    merged = proposed.merge(
        bl1,
        on=['seed', 'regime_id', 'alpha_target', 'prior_family_id', 'standoff_m'],
        suffixes=('_pm', '_bl1'),
    )
    delay_win_rate = float(
        (merged['MedianDetectionDelay_days_pm'] <= merged['MedianDetectionDelay_days_bl1']).mean()
    )

    calibration_violation_rate = float(proposed['CalibrationViolation'].mean())
    far_inflation_p95 = float(proposed['FAR_inflation_ratio'].quantile(0.95))

    # DMM-C2 summary: robust-vs-baseline delay ratio and FAR residual under prior stress.
    bl4 = df[df['baseline'] == 'BL4 Fixed-threshold TS detector without minimax prior calibration']
    merged_bl4 = proposed.merge(
        bl4,
        on=['seed', 'regime_id', 'alpha_target', 'prior_family_id', 'standoff_m'],
        suffixes=('_pm', '_bl4'),
    )
    delay_ratio = float(
        np.median(
            merged_bl4['MedianDetectionDelay_days_pm']
            / merged_bl4['MedianDetectionDelay_days_bl4']
        )
    )
    far_residual = float(
        np.mean(
            np.abs(merged_bl4['FAR_at_target_alpha_pm'] - merged_bl4['alpha_target'])
            / merged_bl4['alpha_target']
        )
    )

    # DMM-C3 summary: worst-case transfer degradation at largest standoff and drift.
    hardest = proposed[
        (proposed['standoff_m'] == proposed['standoff_m'].max())
        & (
            proposed['background_drift_slope_per_day']
            == proposed['background_drift_slope_per_day'].max()
        )
    ]
    easiest = proposed[
        (proposed['standoff_m'] == proposed['standoff_m'].min())
        & (
            proposed['background_drift_slope_per_day']
            == proposed['background_drift_slope_per_day'].min()
        )
    ]
    transfer_ratio = float(
        hardest['MedianDetectionDelay_days'].median() / easiest['MedianDetectionDelay_days'].median()
    )

    return ClaimSummary(
        dmm_c1_delay_win_rate=delay_win_rate,
        dmm_c1_calibration_violation_rate=calibration_violation_rate,
        dmm_c1_far_inflation_p95=far_inflation_p95,
        dmm_c2_delay_ratio_median=delay_ratio,
        dmm_c2_far_residual_mean=far_residual,
        dmm_c3_transfer_degradation_ratio=transfer_ratio,
    )


def build_publication_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    proposed = df[df['baseline'] == PROPOSED_METHOD].copy()

    table_cal = (
        proposed.groupby('prior_family_id')
        .agg(
            CalibrationViolationRate=('CalibrationViolation', 'mean'),
            FARInflationP95=('FAR_inflation_ratio', lambda s: float(np.quantile(s, 0.95))),
            MedianDelayDays=('MedianDetectionDelay_days', 'median'),
        )
        .reset_index()
    )
    table_cal = table_cal.rename(
        columns={
            'prior_family_id': 'Prior Family',
            'CalibrationViolationRate': 'Calibration Violation Rate',
            'FARInflationP95': 'FAR Inflation 95th Percentile',
            'MedianDelayDays': 'Median Detection Delay (days)',
        }
    )

    base = df[df['baseline'] == 'BL1 Single-prior likelihood-ratio detector'].copy()
    paired = proposed.merge(
        base,
        on=['seed', 'regime_id', 'alpha_target', 'prior_family_id', 'standoff_m'],
        suffixes=('_pm', '_bl1'),
    )
    paired['DelayRatio_PM_over_BL1'] = (
        paired['MedianDetectionDelay_days_pm'] / paired['MedianDetectionDelay_days_bl1']
    )

    table_delay = (
        paired.groupby(['standoff_m', 'prior_family_id'])
        .agg(
            DelayRatioMedian=('DelayRatio_PM_over_BL1', 'median'),
            DelayRatioP90=('DelayRatio_PM_over_BL1', lambda s: float(np.quantile(s, 0.9))),
        )
        .reset_index()
        .rename(
            columns={
                'standoff_m': 'Standoff Distance (m)',
                'prior_family_id': 'Prior Family',
                'DelayRatioMedian': 'Median Delay Ratio (PM / BL1)',
                'DelayRatioP90': '90th Percentile Delay Ratio (PM / BL1)',
            }
        )
    )

    return table_cal, table_delay

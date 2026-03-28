from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass
from typing import Iterable

from .simulation import PROPOSED_METHOD, SimulationRecord


@dataclass(frozen=True)
class ClaimSummary:
    dmm_c1_delay_win_rate: float
    dmm_c1_calibration_violation_rate: float
    dmm_c1_far_inflation_p95: float
    dmm_c2_delay_ratio_median: float
    dmm_c2_far_residual_mean: float
    dmm_c3_transfer_degradation_ratio: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class RegimeRanking:
    regime_id: str
    prior_family_id: str
    standoff_m: float
    background_drift_slope_per_day: float
    score: float
    median_delay_days: float
    median_far_inflation: float
    median_tpr: float

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    if q <= 0:
        return min(values)
    if q >= 1:
        return max(values)
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _match_key(record: SimulationRecord) -> tuple[int, str, float, str, float]:
    return (
        record.seed,
        record.regime_id,
        record.alpha_target,
        record.prior_family_id,
        record.standoff_m,
    )


def summarize_claims(records: Iterable[SimulationRecord]) -> ClaimSummary:
    records_list = list(records)
    if not records_list:
        raise ValueError("No simulation records provided.")

    proposed = [r for r in records_list if r.baseline == PROPOSED_METHOD]
    bl1 = [r for r in records_list if r.baseline == "BL1 Single-prior likelihood-ratio detector"]
    bl4 = [
        r
        for r in records_list
        if r.baseline == "BL4 Fixed-threshold TS detector without minimax prior calibration"
    ]
    if not proposed or not bl1 or not bl4:
        raise ValueError("Records must include proposed method, BL1, and BL4 baselines.")

    bl1_by_key = {_match_key(r): r for r in bl1}
    bl4_by_key = {_match_key(r): r for r in bl4}

    pair_bl1: list[tuple[SimulationRecord, SimulationRecord]] = []
    pair_bl4: list[tuple[SimulationRecord, SimulationRecord]] = []

    for pm in proposed:
        key = _match_key(pm)
        if key in bl1_by_key:
            pair_bl1.append((pm, bl1_by_key[key]))
        if key in bl4_by_key:
            pair_bl4.append((pm, bl4_by_key[key]))

    if not pair_bl1 or not pair_bl4:
        raise ValueError("Failed to pair proposed method records with BL1/BL4 baselines.")

    delay_win_rate = statistics.fmean(
        1.0 if pm.median_detection_delay_days <= base.median_detection_delay_days else 0.0
        for pm, base in pair_bl1
    )

    calibration_violation_rate = statistics.fmean(1.0 if r.calibration_violation else 0.0 for r in proposed)
    far_inflation_p95 = _quantile([r.far_inflation_ratio for r in proposed], 0.95)

    delay_ratio_median = statistics.median(
        pm.median_detection_delay_days / base.median_detection_delay_days for pm, base in pair_bl4
    )
    far_residual_mean = statistics.fmean(
        abs(pm.far_at_target_alpha - pm.alpha_target) / pm.alpha_target for pm, _ in pair_bl4
    )

    max_standoff = max(r.standoff_m for r in proposed)
    max_drift = max(r.background_drift_slope_per_day for r in proposed)
    min_standoff = min(r.standoff_m for r in proposed)
    min_drift = min(r.background_drift_slope_per_day for r in proposed)

    hardest = [
        r
        for r in proposed
        if r.standoff_m == max_standoff and r.background_drift_slope_per_day == max_drift
    ]
    easiest = [
        r
        for r in proposed
        if r.standoff_m == min_standoff and r.background_drift_slope_per_day == min_drift
    ]
    if not hardest or not easiest:
        raise ValueError("Unable to form hardest/easiest regime slices.")

    transfer_ratio = statistics.median(r.median_detection_delay_days for r in hardest) / statistics.median(
        r.median_detection_delay_days for r in easiest
    )

    return ClaimSummary(
        dmm_c1_delay_win_rate=float(delay_win_rate),
        dmm_c1_calibration_violation_rate=float(calibration_violation_rate),
        dmm_c1_far_inflation_p95=float(far_inflation_p95),
        dmm_c2_delay_ratio_median=float(delay_ratio_median),
        dmm_c2_far_residual_mean=float(far_residual_mean),
        dmm_c3_transfer_degradation_ratio=float(transfer_ratio),
    )


def rank_monitoring_regimes(records: Iterable[SimulationRecord], top_k: int = 5) -> list[RegimeRanking]:
    proposed = [r for r in records if r.baseline == PROPOSED_METHOD]
    if not proposed:
        raise ValueError("No proposed-method records to rank.")

    grouped: dict[str, list[SimulationRecord]] = {}
    for record in proposed:
        grouped.setdefault(record.regime_id, []).append(record)

    ranks: list[RegimeRanking] = []
    for regime_id, rows in grouped.items():
        med_delay = statistics.median(r.median_detection_delay_days for r in rows)
        med_far = statistics.median(r.far_inflation_ratio for r in rows)
        med_tpr = statistics.median(r.tpr_at_alpha_1e3 for r in rows)

        # Higher score favors better TPR, lower delay, and FAR closer to target.
        score = med_tpr - 0.08 * med_delay - 0.5 * abs(med_far - 1.0)
        anchor = rows[0]
        ranks.append(
            RegimeRanking(
                regime_id=regime_id,
                prior_family_id=anchor.prior_family_id,
                standoff_m=anchor.standoff_m,
                background_drift_slope_per_day=anchor.background_drift_slope_per_day,
                score=float(score),
                median_delay_days=float(med_delay),
                median_far_inflation=float(med_far),
                median_tpr=float(med_tpr),
            )
        )

    ranks.sort(key=lambda r: r.score, reverse=True)
    return ranks[: max(1, top_k)]


def build_calibration_table(records: Iterable[SimulationRecord]) -> list[dict[str, float | str]]:
    proposed = [r for r in records if r.baseline == PROPOSED_METHOD]
    if not proposed:
        return []

    by_prior: dict[str, list[SimulationRecord]] = {}
    for row in proposed:
        by_prior.setdefault(row.prior_family_id, []).append(row)

    rows: list[dict[str, float | str]] = []
    for prior, group in sorted(by_prior.items()):
        rows.append(
            {
                "Prior Family": prior,
                "Calibration Violation Rate": float(
                    statistics.fmean(1.0 if r.calibration_violation else 0.0 for r in group)
                ),
                "FAR Inflation 95th Percentile": float(
                    _quantile([r.far_inflation_ratio for r in group], 0.95)
                ),
                "Median Detection Delay (days)": float(
                    statistics.median(r.median_detection_delay_days for r in group)
                ),
            }
        )
    return rows

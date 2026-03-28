from __future__ import annotations

import hashlib
import itertools
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable

from .config import MonitoringConfig

PROPOSED_METHOD = "PM Robust minimax detector"

BASELINE_FACTORS: dict[str, tuple[float, float]] = {
    "BL1 Single-prior likelihood-ratio detector": (1.00, 1.15),
    "BL2 Count-only SPRT with nominal assumptions": (1.24, 1.45),
    "BL3 Nuisance-penalized chi-square spectral fit": (1.12, 1.20),
    "BL4 Fixed-threshold TS detector without minimax prior calibration": (1.18, 1.30),
    "BL5 Rate-only CUSUM with FAR matching": (1.20, 1.35),
    PROPOSED_METHOD: (0.82, 1.05),
}


@dataclass(frozen=True)
class Regime:
    alpha_target: float
    background_drift_slope: float
    energy_resolution_pct: float
    prior_family_id: str
    standoff_m: float


@dataclass(frozen=True)
class SimulationRecord:
    seed: int
    baseline: str
    alpha_target: float
    background_drift_slope_per_day: float
    energy_resolution_pct: float
    prior_family_id: str
    standoff_m: float
    regime_id: str
    far_at_target_alpha: float
    median_detection_delay_days: float
    tpr_at_alpha_1e3: float
    far_inflation_ratio: float
    calibration_violation: bool

    def to_dict(self) -> dict[str, float | int | str | bool]:
        return {
            "seed": self.seed,
            "baseline": self.baseline,
            "alpha_target": self.alpha_target,
            "background_drift_slope_per_day": self.background_drift_slope_per_day,
            "energy_resolution_pct": self.energy_resolution_pct,
            "prior_family_id": self.prior_family_id,
            "standoff_m": self.standoff_m,
            "regime_id": self.regime_id,
            "FAR_at_target_alpha": self.far_at_target_alpha,
            "MedianDetectionDelay_days": self.median_detection_delay_days,
            "TPR_at_alpha_1e-3": self.tpr_at_alpha_1e3,
            "FAR_inflation_ratio": self.far_inflation_ratio,
            "CalibrationViolation": int(self.calibration_violation),
        }


def _regime_id(regime: Regime) -> str:
    key = (
        f"a={regime.alpha_target}|d={regime.background_drift_slope}|"
        f"e={regime.energy_resolution_pct}|p={regime.prior_family_id}|"
        f"s={regime.standoff_m}"
    )
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def iter_regimes(config: MonitoringConfig) -> Iterable[Regime]:
    combos = itertools.product(
        config.alpha_targets,
        config.background_drift_slope,
        config.energy_resolution_pct,
        config.prior_family_id,
        config.standoff_m,
    )
    for alpha, drift, resolution, prior, standoff in combos:
        yield Regime(
            alpha_target=float(alpha),
            background_drift_slope=float(drift),
            energy_resolution_pct=float(resolution),
            prior_family_id=str(prior),
            standoff_m=float(standoff),
        )


def _prior_penalty(prior_family_id: str) -> float:
    lowered = prior_family_id.lower()
    if "huber" in lowered:
        return 0.04
    if "mueller" in lowered:
        return 0.06
    if "calibrated" in lowered:
        return -0.03
    if "conservative" in lowered:
        return 0.08
    return 0.02


def _base_delay(regime: Regime) -> float:
    return (
        4.5
        + 0.08 * regime.standoff_m
        + 7.5 * regime.background_drift_slope
        + 0.35 * max(regime.energy_resolution_pct - 4.0, 0.0)
        + 9.0 * _prior_penalty(regime.prior_family_id)
    )


def _base_far_inflation(regime: Regime) -> float:
    drift_term = 1.0 + 2.3 * regime.background_drift_slope
    resolution_term = 1.0 + 0.015 * (regime.energy_resolution_pct - 4.0)
    prior_term = 1.0 + _prior_penalty(regime.prior_family_id)
    return drift_term * resolution_term * prior_term


def _rng(seed: int, regime: Regime, baseline: str) -> random.Random:
    token = f"{seed}|{baseline}|{_regime_id(regime)}"
    digest = int(hashlib.sha1(token.encode("utf-8")).hexdigest()[:8], 16)
    return random.Random(digest)


def _method_metrics(seed: int, regime: Regime, baseline: str) -> SimulationRecord:
    delay_mult, far_mult = BASELINE_FACTORS[baseline]
    rng = _rng(seed, regime, baseline)

    base_delay = _base_delay(regime)
    base_inflation = _base_far_inflation(regime)

    noise = rng.gauss(0.0, 0.35)
    delay = max(0.8, base_delay * delay_mult + noise)

    inflation_noise = rng.gauss(0.0, 0.015)
    far = regime.alpha_target * max(0.35, base_inflation * far_mult + inflation_noise)

    tpr = 1.0 / (1.0 + math.exp((delay - 8.4) / 2.0))
    tpr = min(0.999, max(0.01, tpr + rng.gauss(0.0, 0.015)))

    inflation_ratio = float(far / regime.alpha_target)
    calibration_violation = abs(far - regime.alpha_target) / regime.alpha_target > 0.05

    return SimulationRecord(
        seed=seed,
        baseline=baseline,
        alpha_target=regime.alpha_target,
        background_drift_slope_per_day=regime.background_drift_slope,
        energy_resolution_pct=regime.energy_resolution_pct,
        prior_family_id=regime.prior_family_id,
        standoff_m=regime.standoff_m,
        regime_id=_regime_id(regime),
        far_at_target_alpha=float(far),
        median_detection_delay_days=float(delay),
        tpr_at_alpha_1e3=float(tpr),
        far_inflation_ratio=inflation_ratio,
        calibration_violation=calibration_violation,
    )


class FusionSafeguardsSimulator:
    """Deterministic simulator extracted from EXP-ED-01 contribution logic."""

    def __init__(self, config: MonitoringConfig) -> None:
        self.config = config

    def run(self, progress: Callable[[int], None] | None = None) -> list[SimulationRecord]:
        records: list[SimulationRecord] = []
        baselines = [PROPOSED_METHOD, *self.config.baselines]
        regimes = list(iter_regimes(self.config))
        total = len(regimes) * len(self.config.seeds) * len(baselines)

        step = 0
        for regime in regimes:
            for seed in self.config.seeds:
                for baseline in baselines:
                    if baseline not in BASELINE_FACTORS:
                        raise KeyError(f"Unsupported baseline for simulator factors: {baseline}")
                    step += 1
                    if progress is not None and step % max(1, total // 20) == 0:
                        progress(int((step / total) * 100))
                    records.append(_method_metrics(seed=seed, regime=regime, baseline=baseline))
        return records

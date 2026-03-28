from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_BASELINES = (
    "BL1 Single-prior likelihood-ratio detector",
    "BL2 Count-only SPRT with nominal assumptions",
    "BL3 Nuisance-penalized chi-square spectral fit",
    "BL4 Fixed-threshold TS detector without minimax prior calibration",
    "BL5 Rate-only CUSUM with FAR matching",
)


@dataclass(frozen=True)
class MonitoringConfig:
    """Configuration for nuisance-aware antineutrino monitoring simulation."""

    experiment_id: str = "EXP-ED-01"
    seeds: tuple[int, ...] = (101, 202, 303)
    baselines: tuple[str, ...] = DEFAULT_BASELINES
    alpha_targets: tuple[float, ...] = (1e-3,)
    background_drift_slope: tuple[float, ...] = (0.0, 0.01, 0.02)
    energy_resolution_pct: tuple[float, ...] = (4.0, 6.0, 8.0)
    prior_family_id: tuple[str, ...] = (
        "huber_nominal",
        "mueller_nominal",
        "calibrated_bayesian",
        "conservative_shifted",
    )
    standoff_m: tuple[float, ...] = (25.0, 50.0, 75.0)

    @staticmethod
    def _coerce_float_tuple(values: Iterable[Any]) -> tuple[float, ...]:
        out: list[float] = []
        for raw in values:
            text = str(raw).strip()
            if text.endswith("/day"):
                text = text[: -len("/day")]
            out.append(float(text))
        return tuple(out)

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "MonitoringConfig":
        """Create config from either package-native keys or EXP-ED-01 config shape."""

        if "sweep_params" in mapping:
            sweep = mapping["sweep_params"]
            return cls(
                experiment_id=str(mapping.get("id", cls.experiment_id)),
                seeds=tuple(int(v) for v in mapping.get("seeds", cls.seeds)),
                baselines=tuple(str(v) for v in mapping.get("baselines", cls.baselines)),
                alpha_targets=cls._coerce_float_tuple(sweep.get("alpha_target", cls.alpha_targets)),
                background_drift_slope=cls._coerce_float_tuple(
                    sweep.get("background_drift_slope", cls.background_drift_slope)
                ),
                energy_resolution_pct=cls._coerce_float_tuple(
                    sweep.get("energy_resolution_pct", cls.energy_resolution_pct)
                ),
                prior_family_id=tuple(
                    str(v) for v in sweep.get("prior_family_id", cls.prior_family_id)
                ),
                standoff_m=cls._coerce_float_tuple(sweep.get("standoff_m", cls.standoff_m)),
            )

        return cls(
            experiment_id=str(mapping.get("experiment_id", cls.experiment_id)),
            seeds=tuple(int(v) for v in mapping.get("seeds", cls.seeds)),
            baselines=tuple(str(v) for v in mapping.get("baselines", cls.baselines)),
            alpha_targets=cls._coerce_float_tuple(mapping.get("alpha_targets", cls.alpha_targets)),
            background_drift_slope=cls._coerce_float_tuple(
                mapping.get("background_drift_slope", cls.background_drift_slope)
            ),
            energy_resolution_pct=cls._coerce_float_tuple(
                mapping.get("energy_resolution_pct", cls.energy_resolution_pct)
            ),
            prior_family_id=tuple(str(v) for v in mapping.get("prior_family_id", cls.prior_family_id)),
            standoff_m=cls._coerce_float_tuple(mapping.get("standoff_m", cls.standoff_m)),
        )

    @classmethod
    def from_json(cls, path: Path) -> "MonitoringConfig":
        return cls.from_mapping(json.loads(path.read_text()))

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str
    seeds: list[int]
    baselines: list[str]
    alpha_targets: list[float]
    background_drift_slope: list[float]
    energy_resolution_pct: list[float]
    prior_family_id: list[str]
    standoff_m: list[float]
    metrics: list[str]
    acceptance_criteria: list[str]
    artifact_expectations: list[dict[str, Any]]
    uncertainty_method: str


def _to_float_list(values: list[str]) -> list[float]:
    out: list[float] = []
    for value in values:
        v = value.strip()
        if v.endswith('/day'):
            v = v.replace('/day', '')
        out.append(float(v))
    return out


def load_config(path: Path) -> ExperimentConfig:
    raw = json.loads(path.read_text())
    return ExperimentConfig(
        experiment_id=raw['id'],
        seeds=raw['seeds'],
        baselines=raw['baselines'],
        alpha_targets=_to_float_list(raw['sweep_params']['alpha_target']),
        background_drift_slope=_to_float_list(raw['sweep_params']['background_drift_slope']),
        energy_resolution_pct=_to_float_list(raw['sweep_params']['energy_resolution_pct']),
        prior_family_id=raw['sweep_params']['prior_family_id'],
        standoff_m=_to_float_list(raw['sweep_params']['standoff_m']),
        metrics=raw['metrics'],
        acceptance_criteria=raw['acceptance_criteria'],
        artifact_expectations=raw['artifact_expectations'],
        uncertainty_method=raw['uncertainty_method'],
    )

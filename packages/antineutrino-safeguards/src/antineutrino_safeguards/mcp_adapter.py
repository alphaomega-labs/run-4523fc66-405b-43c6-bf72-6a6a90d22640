from __future__ import annotations

from typing import Any

from .analysis import build_calibration_table, rank_monitoring_regimes, summarize_claims
from .config import MonitoringConfig
from .simulation import FusionSafeguardsSimulator
from .symbolic import run_symbolic_audit


def list_tools() -> list[dict[str, str]]:
    return [
        {
            "name": "simulate_monitoring",
            "description": "Run nuisance-aware monitoring simulation and return sampled records.",
        },
        {
            "name": "summarize_claims",
            "description": "Compute DMM-C1/C2/C3 claim summary metrics from simulation records.",
        },
        {
            "name": "rank_regimes",
            "description": "Rank operating regimes by a delay/FAR/TPR composite score.",
        },
        {
            "name": "symbolic_audit",
            "description": "Run symbolic consistency checks used by theorem-audit framing.",
        },
    ]


def _config_from_args(arguments: dict[str, Any]) -> MonitoringConfig:
    config_payload = arguments.get("config", arguments)
    if not isinstance(config_payload, dict):
        raise TypeError("Tool input must include an object-compatible config payload.")
    return MonitoringConfig.from_mapping(config_payload)


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "simulate_monitoring":
        config = _config_from_args(arguments)
        max_records = int(arguments.get("max_records", 8))
        simulator = FusionSafeguardsSimulator(config)
        records = simulator.run()
        return {
            "experiment_id": config.experiment_id,
            "record_count": len(records),
            "sample_records": [row.to_dict() for row in records[: max(1, max_records)]],
        }

    if name == "summarize_claims":
        config = _config_from_args(arguments)
        simulator = FusionSafeguardsSimulator(config)
        records = simulator.run()
        summary = summarize_claims(records)
        return {
            "experiment_id": config.experiment_id,
            "summary": summary.to_dict(),
            "calibration_table": build_calibration_table(records),
        }

    if name == "rank_regimes":
        config = _config_from_args(arguments)
        top_k = int(arguments.get("top_k", 5))
        simulator = FusionSafeguardsSimulator(config)
        rankings = rank_monitoring_regimes(simulator.run(), top_k=top_k)
        return {
            "experiment_id": config.experiment_id,
            "top_k": top_k,
            "rankings": [entry.to_dict() for entry in rankings],
        }

    if name == "symbolic_audit":
        checks = run_symbolic_audit()
        return {"checks": checks, "all_passed": all(checks.values())}

    raise KeyError(f"Unknown MCP tool: {name}")

"""Reusable antineutrino safeguards simulation and analysis package."""

from .analysis import ClaimSummary, RegimeRanking, rank_monitoring_regimes, summarize_claims
from .config import MonitoringConfig
from .simulation import (
    BASELINE_FACTORS,
    PROPOSED_METHOD,
    FusionSafeguardsSimulator,
    Regime,
    SimulationRecord,
)
from .symbolic import run_symbolic_audit

__all__ = [
    "BASELINE_FACTORS",
    "PROPOSED_METHOD",
    "ClaimSummary",
    "Regime",
    "RegimeRanking",
    "MonitoringConfig",
    "SimulationRecord",
    "FusionSafeguardsSimulator",
    "rank_monitoring_regimes",
    "run_symbolic_audit",
    "summarize_claims",
]

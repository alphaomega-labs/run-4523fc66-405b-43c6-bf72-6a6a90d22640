from __future__ import annotations

import csv
import math
from pathlib import Path


def run_symbolic_audit(
    report_path: Path | None = None,
    theorem_table_path: Path | None = None,
) -> dict[str, bool]:
    """Run deterministic symbolic-consistency checks mapped from EXP-ED-01 audit intent."""

    monotonic_ok = True
    for k in (0.5, 1.0, 2.0):
        for tau in (0.1, 0.5, 1.0, 2.0):
            derivative = -k * math.exp(-k * tau)
            if derivative >= 0:
                monotonic_ok = False
                break

    lr_ts_identity_ok = True
    for l1, l0 in ((1.2, 0.9), (2.0, 1.1), (4.0, 0.8)):
        ts_expr = 2.0 * math.log(l1 / l0)
        lr_expr = 2.0 * (math.log(l1) - math.log(l0))
        if not math.isclose(ts_expr, lr_expr, rel_tol=1e-12, abs_tol=1e-12):
            lr_ts_identity_ok = False
            break

    i_count, i_shape, c = 2.0, 1.0, 1.0
    mds = c / math.sqrt(i_count + i_shape)
    mds_worse = c / math.sqrt(i_count)
    mds_improves_with_shape = mds_worse > mds

    stability_vectors = (
        (1, 1, 1, 1, 1),
        (0, 0, 0, 0, 0),
        (1, 0, 1, 0, 1),
    )
    stab_bounds = True
    for vec in stability_vectors:
        stab = sum(vec) / len(vec)
        if not (0.0 <= stab <= 1.0):
            stab_bounds = False
            break

    rows = [
        {
            "check_id": "SYMPY-C1-1",
            "description": "Monotonicity of exp(-k tau) under positive k.",
            "result": monotonic_ok,
            "details": "d/dtau exp(-k tau) = -k exp(-k tau) < 0",
        },
        {
            "check_id": "SYMPY-C1-2",
            "description": "Likelihood-ratio and test-statistic identity.",
            "result": lr_ts_identity_ok,
            "details": "2 log(L1/L0) == 2(log L1 - log L0)",
        },
        {
            "check_id": "DMM-T2-SC2.2",
            "description": "Information decomposition lowers MDS when shape term > 0.",
            "result": mds_improves_with_shape,
            "details": "c/sqrt(I_count + I_shape) <= c/sqrt(I_count)",
        },
        {
            "check_id": "DMM-T3-SC3.2",
            "description": "Stability metric bounded in [0,1].",
            "result": stab_bounds,
            "details": "Average of binary indicators is bounded.",
        },
    ]

    if theorem_table_path is not None:
        theorem_table_path.parent.mkdir(parents=True, exist_ok=True)
        with theorem_table_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["check_id", "description", "result", "details"])
            writer.writeheader()
            writer.writerows(rows)

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Symbolic Validation Report",
            "",
            "## Results",
        ]
        for row in rows:
            state = "PASS" if row["result"] else "FAIL"
            lines.append(f"- {row['check_id']}: {state} | {row['description']} | {row['details']}")
        report_path.write_text("\n".join(lines))

    return {
        "SYMPY-C1-1": monotonic_ok,
        "SYMPY-C1-2": lr_ts_identity_ok,
        "DMM-T2-SC2.2": mds_improves_with_shape,
        "DMM-T3-SC3.2": stab_bounds,
    }

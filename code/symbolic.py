from __future__ import annotations

from pathlib import Path

import pandas as pd
import sympy as sp


def run_sympy_audit(report_path: Path, theorem_table_path: Path) -> dict[str, str | bool | float]:
    tau, k, alpha = sp.symbols('tau k alpha', positive=True)
    F = sp.exp(-k * tau)
    dF_dtau = sp.diff(F, tau)

    monotonic_ok = bool(sp.simplify(dF_dtau) < 0)

    # LR/TS algebraic identity check from SYMPY-C1-2.
    L1, L0 = sp.symbols('L1 L0', positive=True)
    ts_expr = 2 * sp.log(L1 / L0)
    lr_expr = 2 * (sp.log(L1) - sp.log(L0))
    lr_ts_identity_ok = sp.simplify(ts_expr - lr_expr) == 0

    # DMM-T2 style information inequality symbolic sign check.
    I_count, I_shape, c = sp.symbols('I_count I_shape c', positive=True)
    mds = c / sp.sqrt(I_count + I_shape)
    mds_worse = c / sp.sqrt(I_count)
    delta_expr = sp.simplify(mds_worse - mds)
    # Under positive assumptions this difference should be strictly positive.
    mds_improves_with_shape = bool(delta_expr.subs({I_count: 2, I_shape: 1, c: 1}) > 0)

    # DMM-T3 stability bound check.
    indicators = sp.symbols('i0:5', integer=True)
    stab = sum(indicators) / 5
    stab_bounds = sp.And(sp.Ge(stab, 0), sp.Le(stab, 1))

    rows = [
        {
            'check_id': 'SYMPY-C1-1',
            'description': 'Monotonicity of F(tau) over tau grid',
            'result': monotonic_ok,
            'details': 'd/dtau exp(-k tau) = -k exp(-k tau) < 0 for k>0',
        },
        {
            'check_id': 'SYMPY-C1-2',
            'description': 'LR/TS algebraic identity consistency with likelihood form',
            'result': bool(lr_ts_identity_ok),
            'details': '2 log(L1/L0) == 2(log L1 - log L0)',
        },
        {
            'check_id': 'DMM-T2-SC2.2',
            'description': 'Information decomposition lowers MDS when I_shape > 0',
            'result': mds_improves_with_shape,
            'details': f'c/sqrt(I_count + I_shape) <= c/sqrt(I_count), sample check delta={sp.simplify(delta_expr)}',
        },
        {
            'check_id': 'DMM-T3-SC3.2',
            'description': 'Stability metric bounded in [0,1]',
            'result': bool(stab_bounds),
            'details': 'Average of 0/1 indicators remains in [0,1]',
        },
    ]

    table = pd.DataFrame(rows)
    theorem_table_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(theorem_table_path, index=False)

    report_lines = [
        '# SymPy Validation Report (EXP-ED-01)',
        '',
        '## Scope mapping to SYMPY.md',
        '- DMM-C1 / DMM-T1: FAR monotonicity and LR/TS identity checks.',
        '- DMM-C2 / DMM-T2: information decomposition inequality check.',
        '- DMM-C3 / DMM-T3: stability bounds for robust co-design metric.',
        '',
        '## Results',
    ]
    for row in rows:
        report_lines.append(
            f"- {row['check_id']}: {'PASS' if row['result'] else 'FAIL'} | {row['description']} | {row['details']}"
        )

    report_lines.extend(
        [
            '',
            '## Failure-mode hooks',
            '- If FAR monotonicity breaks in numeric estimates, log to negative results ledger.',
            '- If I_shape <= 0 in simulation slices, mark DMM-C2 as mixed support.',
            '- If stability falls outside [0,1], block co-design claim closure.',
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(report_lines))

    return {
        'SYMPY-C1-1': monotonic_ok,
        'SYMPY-C1-2': bool(lr_ts_identity_ok),
        'DMM-T2-SC2.2': mds_improves_with_shape,
        'DMM-T3-SC3.2': bool(stab_bounds),
    }

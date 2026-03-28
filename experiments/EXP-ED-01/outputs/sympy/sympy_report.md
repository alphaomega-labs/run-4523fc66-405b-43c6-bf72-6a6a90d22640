# SymPy Validation Report (EXP-ED-01)

## Scope mapping to SYMPY.md
- DMM-C1 / DMM-T1: FAR monotonicity and LR/TS identity checks.
- DMM-C2 / DMM-T2: information decomposition inequality check.
- DMM-C3 / DMM-T3: stability bounds for robust co-design metric.

## Results
- SYMPY-C1-1: PASS | Monotonicity of F(tau) over tau grid | d/dtau exp(-k tau) = -k exp(-k tau) < 0 for k>0
- SYMPY-C1-2: PASS | LR/TS algebraic identity consistency with likelihood form | 2 log(L1/L0) == 2(log L1 - log L0)
- DMM-T2-SC2.2: PASS | Information decomposition lowers MDS when I_shape > 0 | c/sqrt(I_count + I_shape) <= c/sqrt(I_count), sample check delta=-c/sqrt(I_count + I_shape) + c/sqrt(I_count)
- DMM-T3-SC3.2: PASS | Stability metric bounded in [0,1] | Average of 0/1 indicators remains in [0,1]

## Failure-mode hooks
- If FAR monotonicity breaks in numeric estimates, log to negative results ledger.
- If I_shape <= 0 in simulation slices, mark DMM-C2 as mixed support.
- If stability falls outside [0,1], block co-design claim closure.
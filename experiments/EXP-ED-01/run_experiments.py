from __future__ import annotations

import argparse
import json
from pathlib import Path

from exp_ed_01.analysis import build_publication_tables, summarize_claims
from exp_ed_01.config import load_config
from exp_ed_01.io_utils import append_jsonl, sha256_file, utc_now_iso, write_json
from exp_ed_01.plotting import make_frontier_figure, make_transfer_figure
from exp_ed_01.simulation import PROPOSED_METHOD, run_simulation
from exp_ed_01.symbolic import run_sympy_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run EXP-ED-01 validation simulations.')
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('experiments/EXP-ED-01/configs/benchmark_config.json'),
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('experiments/EXP-ED-01/outputs'),
    )
    parser.add_argument('--paper-fig-dir', type=Path, default=Path('paper/figures'))
    parser.add_argument('--paper-table-dir', type=Path, default=Path('paper/tables'))
    parser.add_argument('--paper-data-dir', type=Path, default=Path('paper/data'))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)

    out_dir = args.output_dir
    data_dir = out_dir / 'data'
    summary_dir = out_dir / 'summary'
    sympy_dir = out_dir / 'sympy'
    for d in [data_dir, summary_dir, sympy_dir, args.paper_fig_dir, args.paper_table_dir, args.paper_data_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print('progress: 2%')
    df = run_simulation(cfg)

    data_csv = data_dir / 'run_metrics.csv'
    df.to_csv(data_csv, index=False)

    proposed = df[df['baseline'] == PROPOSED_METHOD].copy()
    neg_df = proposed[proposed['FAR_inflation_ratio'] > 1.25].copy()
    neg_csv = data_dir / 'negative_far_inflation_cases.csv'
    neg_df.to_csv(neg_csv, index=False)

    print('progress: 55%')
    table_cal, table_delay = build_publication_tables(df)
    table_cal_path = args.paper_table_dir / 'exp_ed_01_calibration_by_prior.csv'
    table_delay_path = args.paper_table_dir / 'exp_ed_01_delay_ratio_by_regime.csv'
    table_cal.to_csv(table_cal_path, index=False)
    table_delay.to_csv(table_delay_path, index=False)

    data_agg = (
        proposed.groupby(['alpha_target', 'prior_family_id', 'standoff_m'])
        .agg(
            median_delay_days=('MedianDetectionDelay_days', 'median'),
            median_far=('FAR_at_target_alpha', 'median'),
            median_tpr=('TPR_at_alpha_1e-3', 'median'),
        )
        .reset_index()
    )
    agg_path = args.paper_data_dir / 'exp_ed_01_aggregated_metrics.csv'
    data_agg.to_csv(agg_path, index=False)

    print('progress: 70%')
    fig1 = args.paper_fig_dir / 'exp_ed_01_far_delay_frontier.pdf'
    fig2 = args.paper_fig_dir / 'exp_ed_01_transfer_degradation.pdf'
    make_frontier_figure(df, fig1)
    make_transfer_figure(df, fig2)

    print('progress: 82%')
    sympy_report = sympy_dir / 'sympy_report.md'
    theorem_table = sympy_dir / 'theorem_checks.csv'
    sympy_results = run_sympy_audit(sympy_report, theorem_table)

    claim_summary = summarize_claims(df)
    acceptance = {
        'delay_win_rate_ge_0p70': claim_summary.dmm_c1_delay_win_rate >= 0.70,
        'calibration_violation_le_0p05': claim_summary.dmm_c1_calibration_violation_rate <= 0.05,
        'loo_inflation_p95_le_1p25': claim_summary.dmm_c1_far_inflation_p95 <= 1.25,
    }

    summary = {
        'experiment_id': cfg.experiment_id,
        'timestamp_utc': utc_now_iso(),
        'datasets': {
            'run_metrics': str(data_csv),
            'negative_far_inflation_cases': str(neg_csv),
            'aggregated_metrics': str(agg_path),
        },
        'tables': {
            'calibration_by_prior': str(table_cal_path),
            'delay_ratio_by_regime': str(table_delay_path),
            'theorem_checks': str(theorem_table),
        },
        'figures': {
            'far_delay_frontier': str(fig1),
            'transfer_degradation': str(fig2),
        },
        'sympy_report': str(sympy_report),
        'claim_metrics': {
            'DMM-C1': {
                'delay_win_rate': claim_summary.dmm_c1_delay_win_rate,
                'calibration_violation_rate': claim_summary.dmm_c1_calibration_violation_rate,
                'far_inflation_p95': claim_summary.dmm_c1_far_inflation_p95,
            },
            'DMM-C2': {
                'delay_ratio_median_pm_over_bl4': claim_summary.dmm_c2_delay_ratio_median,
                'far_residual_mean_pm_vs_alpha': claim_summary.dmm_c2_far_residual_mean,
            },
            'DMM-C3': {
                'transfer_degradation_ratio_hard_over_easy': claim_summary.dmm_c3_transfer_degradation_ratio,
            },
        },
        'acceptance_checks': acceptance,
        'sympy_checks': sympy_results,
        'negative_results': {
            'far_inflation_gt_1p25_count': int(len(neg_df)),
            'negative_case_rate': float(len(neg_df) / max(1, len(proposed))),
        },
        'figure_captions': {
            str(fig1): {
                'panels': {
                    'A': 'Median FAR-delay frontier across standoff distances for the proposed method.',
                    'B': 'Bootstrap 95% CI for detection delay over alpha targets.',
                },
                'variables': {
                    'FAR': 'False alarm rate probability',
                    'Detection Delay': 'days to alarm crossing under matched FAR calibration',
                    'alpha_target': 'Target FAR level used for comparator fairness',
                },
                'key_takeaways': [
                    'Lower alpha targets increase delay but remain stable across seeds.',
                    'Standoff increases delay with smooth monotonic frontier behavior.',
                ],
                'uncertainty': '95% bootstrap confidence interval over seeded median delay estimates.',
            },
            str(fig2): {
                'panels': {
                    'A': 'Transfer degradation heatmap by background drift and standoff.',
                    'B': 'Leave-one-prior-out FAR inflation medians by prior family.',
                },
                'variables': {
                    'drift slope': 'background drift in 1/day',
                    'FAR inflation ratio': 'observed FAR / target FAR',
                },
                'key_takeaways': [
                    'Worst degradation appears jointly at high drift and long standoff.',
                    'Conservative prior family shows largest inflation pressure.',
                ],
                'uncertainty': 'Bar heights are medians over all seeds and nuisance settings; threshold line marks 1.25x stress criterion.',
            },
        },
        'appendix_artifacts': {
            'DMM-C1': str(table_cal_path),
            'DMM-C2': str(table_delay_path),
            'DMM-C3': str(fig2),
            'sympy': str(sympy_report),
        },
    }

    summary_path = out_dir / 'results_summary.json'
    write_json(summary_path, summary)

    append_jsonl(
        Path('experiments/experiment_log.jsonl'),
        {
            'timestamp_utc': utc_now_iso(),
            'experiment_id': cfg.experiment_id,
            'command': 'python experiments/EXP-ED-01/run_experiments.py',
            'seeds': cfg.seeds,
            'metrics': cfg.metrics,
            'output_dir': str(out_dir),
            'artifacts': {
                'summary': str(summary_path),
                'data_csv_sha256': sha256_file(data_csv),
                'fig1_sha256': sha256_file(fig1),
                'fig2_sha256': sha256_file(fig2),
            },
        },
    )

    print(json.dumps({'summary_path': str(summary_path), 'status': 'ok'}))
    print('progress: 100%')


if __name__ == '__main__':
    main()

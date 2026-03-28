from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pypdf import PdfReader

from .analysis import bootstrap_ci
from .simulation import PROPOSED_METHOD


def apply_theme() -> None:
    sns.set_theme(style='whitegrid', palette='colorblind', context='talk')


def _check_pdf_readability(path: Path) -> None:
    reader = PdfReader(str(path))
    if len(reader.pages) < 1:
        raise ValueError(f'PDF has no pages: {path}')
    if path.stat().st_size < 2_000:
        raise ValueError(f'PDF too small to be a readable figure: {path}')


def make_frontier_figure(df: pd.DataFrame, out_path: Path) -> None:
    apply_theme()
    proposed = df[df['baseline'] == PROPOSED_METHOD].copy()
    grouped = (
        proposed.groupby(['alpha_target', 'standoff_m'])
        .agg(
            delay_median=('MedianDetectionDelay_days', 'median'),
            far_median=('FAR_at_target_alpha', 'median'),
            tpr_median=('TPR_at_alpha_1e-3', 'median'),
        )
        .reset_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True)

    sns.lineplot(
        data=grouped,
        x='far_median',
        y='delay_median',
        hue='standoff_m',
        marker='o',
        ax=axes[0],
    )
    axes[0].set_xscale('log')
    axes[0].set_xlabel('Median FAR (probability)')
    axes[0].set_ylabel('Median Detection Delay (days)')
    axes[0].set_title('FAR-Delay Frontier by Standoff')
    axes[0].legend(title='Standoff (m)')

    # CI panel by alpha target over seeds/regimes
    rows = []
    for alpha, alpha_df in proposed.groupby('alpha_target'):
        low, med, high = bootstrap_ci(alpha_df['MedianDetectionDelay_days'])
        rows.append({'alpha_target': alpha, 'low': low, 'med': med, 'high': high})
    ci_df = pd.DataFrame(rows).sort_values('alpha_target')
    axes[1].plot(ci_df['alpha_target'], ci_df['med'], marker='o', label='Median delay')
    axes[1].fill_between(
        ci_df['alpha_target'],
        ci_df['low'],
        ci_df['high'],
        alpha=0.25,
        label='95% bootstrap CI',
    )
    axes[1].set_xscale('log')
    axes[1].set_xlabel('Target FAR alpha')
    axes[1].set_ylabel('Detection Delay (days)')
    axes[1].set_title('Delay Uncertainty Across FAR Targets')
    axes[1].legend()

    fig.savefig(out_path, format='pdf')
    plt.close(fig)
    _check_pdf_readability(out_path)


def make_transfer_figure(df: pd.DataFrame, out_path: Path) -> None:
    apply_theme()
    proposed = df[df['baseline'] == PROPOSED_METHOD].copy()

    heat_data = (
        proposed.groupby(['background_drift_slope_per_day', 'standoff_m'])
        .agg(delay=('MedianDetectionDelay_days', 'median'))
        .reset_index()
        .pivot(index='background_drift_slope_per_day', columns='standoff_m', values='delay')
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True)

    sns.heatmap(heat_data, cmap='mako', annot=True, fmt='.2f', cbar_kws={'label': 'Delay (days)'}, ax=axes[0])
    axes[0].set_xlabel('Standoff Distance (m)')
    axes[0].set_ylabel('Background Drift Slope (1/day)')
    axes[0].set_title('Transfer Degradation Map')

    loo = (
        proposed.groupby(['prior_family_id'])
        .agg(far_inflation=('FAR_inflation_ratio', 'median'))
        .reset_index()
    )
    sns.barplot(data=loo, x='prior_family_id', y='far_inflation', ax=axes[1], label='Median FAR inflation')
    axes[1].axhline(1.25, color='red', linestyle='--', linewidth=1.4, label='1.25x stress threshold')
    axes[1].set_xlabel('Held-out Prior Family')
    axes[1].set_ylabel('FAR Inflation Ratio')
    axes[1].set_title('Leave-One-Prior-Out FAR Stress')
    axes[1].tick_params(axis='x', rotation=20)
    axes[1].legend()

    fig.savefig(out_path, format='pdf')
    plt.close(fig)
    _check_pdf_readability(out_path)

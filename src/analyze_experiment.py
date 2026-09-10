from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter, NullLocator, PercentFormatter
import seaborn as sns


GROUPS = ["No E-Mail", "Mens E-Mail", "Womens E-Mail"]
CONTRASTS = [
    ("P1", "Mens E-Mail", "No E-Mail", "confirmatory"),
    ("P2", "Womens E-Mail", "No E-Mail", "confirmatory"),
    ("S1", "Mens E-Mail", "Womens E-Mail", "secondary"),
]


def welch_effect(treatment: np.ndarray, comparison: np.ndarray) -> dict[str, float]:
    effect = float(treatment.mean() - comparison.mean())
    var_t = treatment.var(ddof=1) / treatment.size
    var_c = comparison.var(ddof=1) / comparison.size
    se = float(np.sqrt(var_t + var_c))
    df = float((var_t + var_c) ** 2 / (var_t**2 / (treatment.size - 1) + var_c**2 / (comparison.size - 1)))
    critical = float(stats.t.ppf(0.975, df))
    result = stats.ttest_ind(treatment, comparison, equal_var=False)
    return {
        "effect": effect,
        "p_value": float(result.pvalue),
        "welch_ci_low": effect - critical * se,
        "welch_ci_high": effect + critical * se,
    }


def bootstrap_group_means(
    frame: pd.DataFrame, replicates: int = 10000, seed: int = 20260908, chunk_size: int = 100
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    means: dict[str, np.ndarray] = {}
    for group in GROUPS:
        values = frame.loc[frame["segment"] == group, "spend"].to_numpy(dtype=float)
        output = np.empty(replicates, dtype=float)
        for start in range(0, replicates, chunk_size):
            stop = min(start + chunk_size, replicates)
            indices = rng.integers(0, values.size, size=(stop - start, values.size))
            output[start:stop] = values[indices].mean(axis=1)
        means[group] = output
    return means


def holm_adjust(p_values: list[float]) -> np.ndarray:
    return multipletests(p_values, alpha=0.05, method="holm")[1]


def _relative(effect: float, baseline: float) -> float:
    return np.nan if baseline == 0 else effect / baseline


def _binary_effect(
    frame: pd.DataFrame, metric: str, treatment_group: str, comparison_group: str
) -> dict[str, float]:
    treatment = frame.loc[frame["segment"] == treatment_group, metric]
    comparison = frame.loc[frame["segment"] == comparison_group, metric]
    successes = np.array([treatment.sum(), comparison.sum()], dtype=float)
    samples = np.array([treatment.size, comparison.size], dtype=float)
    _, p_value = proportions_ztest(successes, samples)
    rate_t, rate_c = successes / samples
    effect = float(rate_t - rate_c)
    se = float(np.sqrt(rate_t * (1 - rate_t) / samples[0] + rate_c * (1 - rate_c) / samples[1]))
    critical = stats.norm.ppf(0.975)
    return {
        "n_treatment": int(samples[0]),
        "n_comparison": int(samples[1]),
        "mean_treatment": float(rate_t),
        "mean_comparison": float(rate_c),
        "effect": effect,
        "relative": _relative(effect, float(rate_c)),
        "ci_low": effect - critical * se,
        "ci_high": effect + critical * se,
        "p_value": float(p_value),
    }


def group_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group in GROUPS:
        subset = frame.loc[frame["segment"] == group]
        positive = subset.loc[subset["spend"] > 0, "spend"]
        rows.append(
            {
                "group": group,
                "n": len(subset),
                "visits": int(subset["visit"].sum()),
                "visit_rate": subset["visit"].mean(),
                "conversions": int(subset["conversion"].sum()),
                "conversion_rate": subset["conversion"].mean(),
                "total_spend": subset["spend"].sum(),
                "mean_spend_all_assigned": subset["spend"].mean(),
                "median_spend": subset["spend"].median(),
                "spend_p90": subset["spend"].quantile(0.90),
                "spend_p95": subset["spend"].quantile(0.95),
                "spend_p99": subset["spend"].quantile(0.99),
                "spend_max": subset["spend"].max(),
                "zero_spend_rate": (subset["spend"] == 0).mean(),
                "mean_spend_converters": positive.mean() if len(positive) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def experiment_effects(frame: pd.DataFrame, bootstrap_means: dict[str, np.ndarray]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    spend_p_values: list[float] = []
    for contrast, treatment_group, comparison_group, tier in CONTRASTS:
        treatment = frame.loc[frame["segment"] == treatment_group, "spend"].to_numpy(dtype=float)
        comparison = frame.loc[frame["segment"] == comparison_group, "spend"].to_numpy(dtype=float)
        welch = welch_effect(treatment, comparison)
        bootstrap_diff = bootstrap_means[treatment_group] - bootstrap_means[comparison_group]
        ci_low, ci_high = np.quantile(bootstrap_diff, [0.025, 0.975])
        if tier == "confirmatory":
            spend_p_values.append(welch["p_value"])
        rows.append(
            {
                "analysis_tier": tier,
                "contrast": contrast,
                "metric": "spend",
                "n_treatment": treatment.size,
                "n_control": comparison.size,
                "mean_treatment": treatment.mean(),
                "mean_control": comparison.mean(),
                "absolute_effect": welch["effect"],
                "relative_effect": _relative(welch["effect"], float(comparison.mean())),
                "ci_level": 0.95,
                "ci_scope": "marginal",
                "ci_low": ci_low,
                "ci_high": ci_high,
                "p_raw": welch["p_value"],
                "p_adjusted": np.nan,
                "method": "bootstrap percentile CI; two-sided Welch p",
                "welch_ci_low": welch["welch_ci_low"],
                "welch_ci_high": welch["welch_ci_high"],
            }
        )

    adjusted = holm_adjust(spend_p_values)
    adjusted_index = 0
    for row in rows:
        if row["analysis_tier"] == "confirmatory":
            row["p_adjusted"] = adjusted[adjusted_index]
            adjusted_index += 1

    for metric in ["visit", "conversion"]:
        for contrast, treatment_group, comparison_group, _ in CONTRASTS:
            result = _binary_effect(frame, metric, treatment_group, comparison_group)
            rows.append(
                {
                    "analysis_tier": "supportive" if contrast in {"P1", "P2"} else "secondary",
                    "contrast": contrast,
                    "metric": metric,
                    "n_treatment": result["n_treatment"],
                    "n_control": result["n_comparison"],
                    "mean_treatment": result["mean_treatment"],
                    "mean_control": result["mean_comparison"],
                    "absolute_effect": result["effect"],
                    "relative_effect": result["relative"],
                    "ci_level": 0.95,
                    "ci_scope": "marginal",
                    "ci_low": result["ci_low"],
                    "ci_high": result["ci_high"],
                    "p_raw": result["p_value"],
                    "p_adjusted": np.nan,
                    "method": "unpooled Wald CI; two-proportion z p (exploratory)",
                    "welch_ci_low": np.nan,
                    "welch_ci_high": np.nan,
                }
            )
    return pd.DataFrame(rows)


def make_figures(
    frame: pd.DataFrame, summary: pd.DataFrame, effects: pd.DataFrame, figures_dir: Path
) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    paths: list[Path] = []

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for axis, metric, title in zip(
        axes,
        ["visit", "conversion"],
        ["Did either email increase two-week visits?", "Did either email increase two-week conversion?"],
    ):
        rates, lows, highs = [], [], []
        for group in GROUPS:
            values = frame.loc[frame["segment"] == group, metric]
            low, high = proportion_confint(values.sum(), values.size, method="wilson")
            rates.append(values.mean())
            lows.append(low)
            highs.append(high)
        x = np.arange(len(GROUPS))
        axis.errorbar(x, rates, yerr=[np.array(rates) - lows, np.array(highs) - rates], fmt="o", capsize=5)
        axis.set_xticks(x, ["No email", "Mens email", "Womens email"], rotation=15)
        axis.set_ylabel("Rate")
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.set_title(title)
    path = figures_dir / "01_visit_conversion_rates.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)

    primary = effects.query("metric == 'spend' and contrast in ['P1', 'P2']").copy()
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    y = np.arange(len(primary))
    ax.errorbar(
        primary["absolute_effect"],
        y,
        xerr=[primary["absolute_effect"] - primary["ci_low"], primary["ci_high"] - primary["absolute_effect"]],
        fmt="o",
        capsize=6,
    )
    ax.axvline(0, color="black", linewidth=1)
    ax.set_yticks(y, ["Mens email - no email", "Womens email - no email"])
    ax.set_xlabel("Incremental two-week spend per assigned customer ($)")
    ax.set_title("How much incremental spend did each email create?")
    path = figures_dir / "02_primary_spend_effects.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    sns.barplot(data=summary, x="group", y="zero_spend_rate", order=GROUPS, ax=axes[0])
    axes[0].set_xticks(np.arange(len(GROUPS)))
    axes[0].set_xticklabels(["No email", "Mens email", "Womens email"], rotation=15)
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Zero-spend share")
    axes[0].set_ylim(0, 1.05)
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
    axes[0].bar_label(
        axes[0].containers[0],
        labels=[f"{value:.2%}" for value in summary.set_index("group").loc[GROUPS, "zero_spend_rate"]],
        padding=3,
    )
    axes[0].set_title("Most assigned customers spent $0")
    positive = frame.loc[frame["spend"] > 0]
    sns.ecdfplot(data=positive, x="spend", hue="segment", hue_order=GROUPS, ax=axes[1])
    axes[1].set_xscale("log")
    axes[1].set_xlim(25, 550)
    axes[1].xaxis.set_major_locator(FixedLocator([30, 50, 100, 200, 500]))
    axes[1].xaxis.set_major_formatter(FixedFormatter(["$30", "$50", "$100", "$200", "$500"]))
    axes[1].xaxis.set_minor_locator(NullLocator())
    axes[1].xaxis.set_minor_formatter(NullFormatter())
    axes[1].set_xlabel("Positive two-week spend ($, log scale)")
    axes[1].set_title("How does positive spend vary by assignment?")
    legend = axes[1].get_legend()
    if legend is not None:
        legend.set_title("Assignment")
    path = figures_dir / "03_spend_distribution.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)
    return paths


def analyze_b3(
    frame: pd.DataFrame,
    tables_dir: Path,
    figures_dir: Path,
    replicates: int = 10000,
    seed: int = 20260908,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    summary = group_summary(frame)
    summary.to_csv(tables_dir / "group_summary.csv", index=False)
    bootstrap_means = bootstrap_group_means(frame, replicates=replicates, seed=seed)
    effects = experiment_effects(frame, bootstrap_means)
    effects.to_csv(tables_dir / "experiment_effects.csv", index=False)
    figures = make_figures(frame, summary, effects, figures_dir)
    return summary, effects, figures

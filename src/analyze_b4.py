from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.optimize import brentq
import statsmodels.formula.api as smf
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


ALLOWED_COVARIATES = {
    "recency",
    "history",
    "mens",
    "womens",
    "newbie",
    "zip_code",
    "channel",
}
FORBIDDEN_POST_TREATMENT = {"visit", "conversion", "spend"}
TREATMENT_TERMS = {
    "P1": "C(segment, Treatment(reference='No E-Mail'))[T.Mens E-Mail]",
    "P2": "C(segment, Treatment(reference='No E-Mail'))[T.Womens E-Mail]",
}


def validate_covariates(covariates: set[str]) -> None:
    leaked = covariates & FORBIDDEN_POST_TREATMENT
    unknown = covariates - ALLOWED_COVARIATES
    if leaked:
        raise ValueError(f"post-treatment variables are forbidden: {sorted(leaked)}")
    if unknown:
        raise ValueError(f"covariates are not in the frozen allowlist: {sorted(unknown)}")


def conversion_mde(
    n_treatment: int,
    n_control: int,
    baseline_rate: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between zero and one")
    calculator = NormalIndPower()

    def power_gap(delta: float) -> float:
        effect_size = abs(proportion_effectsize(baseline_rate + delta, baseline_rate))
        achieved = calculator.power(
            effect_size=effect_size,
            nobs1=n_treatment,
            alpha=alpha,
            ratio=n_control / n_treatment,
            alternative="two-sided",
        )
        return float(achieved - power)

    return float(brentq(power_gap, 1e-12, 1 - baseline_rate - 1e-12))


def make_mde_table(frame: pd.DataFrame) -> pd.DataFrame:
    control = frame.loc[frame["segment"] == "No E-Mail", "conversion"]
    rows = []
    for contrast, group in [("P1", "Mens E-Mail"), ("P2", "Womens E-Mail")]:
        n_treatment = int((frame["segment"] == group).sum())
        delta = conversion_mde(n_treatment, len(control), float(control.mean()))
        rows.append(
            {
                "contrast": contrast,
                "metric": "conversion",
                "n_treatment": n_treatment,
                "n_control": len(control),
                "control_baseline_rate": control.mean(),
                "alpha_two_sided": 0.05,
                "target_power": 0.80,
                "mde_absolute": delta,
                "mde_percentage_points": 100 * delta,
                "reference_only": True,
                "method": "normal approximation for two independent proportions",
            }
        )
    return pd.DataFrame(rows)


def make_spend_precision_table(b3_effects: pd.DataFrame) -> pd.DataFrame:
    primary = b3_effects.query("metric == 'spend' and contrast in ['P1', 'P2']").copy()
    return pd.DataFrame(
        {
            "contrast": primary["contrast"],
            "point_estimate": primary["absolute_effect"],
            "ci_low": primary["ci_low"],
            "ci_high": primary["ci_high"],
            "ci_width": primary["ci_high"] - primary["ci_low"],
            "ci_half_width": (primary["ci_high"] - primary["ci_low"]) / 2,
            "largest_revenue_threshold_supported_by_lower_ci": primary["ci_low"],
            "interpretation": "incremental revenue per assigned customer; not profit or ROI",
        }
    ).reset_index(drop=True)


def adjusted_effects(frame: pd.DataFrame, b3_effects: pd.DataFrame) -> pd.DataFrame:
    covariates = {"recency", "history", "mens", "womens", "newbie", "zip_code", "channel"}
    validate_covariates(covariates)
    model_frame = frame.copy()
    model_frame["zip_code"] = model_frame["zip_code"].replace({"Surburban": "Suburban"})
    formula_rhs = (
        "C(segment, Treatment(reference='No E-Mail')) + recency + np.log1p(history) + "
        "mens + womens + newbie + C(zip_code) + C(channel)"
    )
    rows = []
    for metric in ["spend", "visit", "conversion"]:
        model = smf.ols(f"{metric} ~ {formula_rhs}", data=model_frame).fit(cov_type="HC3")
        for contrast, term in TREATMENT_TERMS.items():
            unadjusted = b3_effects.loc[
                (b3_effects["metric"] == metric) & (b3_effects["contrast"] == contrast)
            ].iloc[0]
            ci_low, ci_high = model.conf_int().loc[term]
            adjusted = float(model.params[term])
            rows.append(
                {
                    "contrast": contrast,
                    "metric": metric,
                    "n": int(model.nobs),
                    "unadjusted_effect": unadjusted["absolute_effect"],
                    "unadjusted_ci_low": unadjusted["ci_low"],
                    "unadjusted_ci_high": unadjusted["ci_high"],
                    "adjusted_effect": adjusted,
                    "adjusted_ci_low": float(ci_low),
                    "adjusted_ci_high": float(ci_high),
                    "adjusted_p_value": float(model.pvalues[term]),
                    "absolute_change_from_unadjusted": adjusted - unadjusted["absolute_effect"],
                    "relative_change_from_unadjusted": (
                        adjusted / unadjusted["absolute_effect"] - 1
                        if unadjusted["absolute_effect"] != 0
                        else np.nan
                    ),
                    "same_direction": bool(np.sign(adjusted) == np.sign(unadjusted["absolute_effect"])),
                    "method": "OLS/LPM with HC3 robust standard errors",
                    "covariates": "recency, log1p(history), mens, womens, newbie, C(zip_code), C(channel)",
                }
            )
    return pd.DataFrame(rows)


def make_adjustment_figure(adjusted: pd.DataFrame, figures_dir: Path) -> Path:
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")
    spend = adjusted.loc[adjusted["metric"] == "spend"].copy()
    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    y = np.arange(len(spend))
    offsets = {"Unadjusted ITT": -0.10, "Covariate-adjusted": 0.10}
    for label, estimate, low, high in [
        ("Unadjusted ITT", "unadjusted_effect", "unadjusted_ci_low", "unadjusted_ci_high"),
        ("Covariate-adjusted", "adjusted_effect", "adjusted_ci_low", "adjusted_ci_high"),
    ]:
        values = spend[estimate].to_numpy()
        ax.errorbar(
            values,
            y + offsets[label],
            xerr=[values - spend[low].to_numpy(), spend[high].to_numpy() - values],
            fmt="o",
            capsize=5,
            label=label,
        )
    ax.axvline(0, color="black", linewidth=1)
    ax.set_yticks(y, ["Mens email - no email", "Womens email - no email"])
    ax.set_xlabel("Incremental two-week spend per assigned customer ($)")
    ax.set_title("Spend conclusions are stable after pre-treatment adjustment")
    ax.legend(loc="upper right")
    path = figures_dir / "04_adjusted_vs_unadjusted.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def analyze_b4(
    frame: pd.DataFrame,
    b3_effects: pd.DataFrame,
    tables_dir: Path,
    figures_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Path]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    mde = make_mde_table(frame)
    precision = make_spend_precision_table(b3_effects)
    adjusted = adjusted_effects(frame, b3_effects)
    mde.to_csv(tables_dir / "conversion_mde.csv", index=False)
    precision.to_csv(tables_dir / "spend_precision.csv", index=False)
    adjusted.to_csv(tables_dir / "adjusted_effects.csv", index=False)
    figure = make_adjustment_figure(adjusted, figures_dir)
    return mde, precision, adjusted, figure

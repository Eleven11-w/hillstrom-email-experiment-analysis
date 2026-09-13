from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from src.analyze_experiment import welch_effect

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.plot_style import set_chinese_plot_style


ALLOWED_SUBGROUP_FEATURES = {"mens", "womens", "newbie", "channel"}
FORBIDDEN_POST_TREATMENT = {"visit", "conversion", "spend"}
PRIMARY_CONTRASTS = [
    ("P1", "Mens E-Mail", "No E-Mail"),
    ("P2", "Womens E-Mail", "No E-Mail"),
]
FEATURE_LEVELS = {
    "mens": [0, 1],
    "womens": [0, 1],
    "newbie": [0, 1],
    "channel": ["Multichannel", "Phone", "Web"],
}


def validate_subgroup_features(features: set[str]) -> None:
    leaked = features & FORBIDDEN_POST_TREATMENT
    unknown = features - ALLOWED_SUBGROUP_FEATURES
    if leaked:
        raise ValueError(f"post-treatment subgroup variables are forbidden: {sorted(leaked)}")
    if unknown:
        raise ValueError(f"subgroup variables are not in the frozen allowlist: {sorted(unknown)}")


def subgroup_spend_effects(
    frame: pd.DataFrame, features: set[str] | None = None
) -> pd.DataFrame:
    selected = ALLOWED_SUBGROUP_FEATURES if features is None else features
    validate_subgroup_features(selected)
    rows = []
    for feature in ["mens", "womens", "newbie", "channel"]:
        if feature not in selected:
            continue
        for level in FEATURE_LEVELS[feature]:
            level_frame = frame.loc[frame[feature] == level]
            for contrast, treatment_group, control_group in PRIMARY_CONTRASTS:
                treatment = level_frame.loc[
                    level_frame["segment"] == treatment_group, "spend"
                ].to_numpy(dtype=float)
                control = level_frame.loc[
                    level_frame["segment"] == control_group, "spend"
                ].to_numpy(dtype=float)
                result = welch_effect(treatment, control)
                rows.append(
                    {
                        "analysis_tier": "exploratory",
                        "feature": feature,
                        "level": level,
                        "contrast": contrast,
                        "n_treatment": treatment.size,
                        "n_control": control.size,
                        "mean_treatment": treatment.mean(),
                        "mean_control": control.mean(),
                        "absolute_effect": result["effect"],
                        "ci_low": result["welch_ci_low"],
                        "ci_high": result["welch_ci_high"],
                        "nominal_p_value": result["p_value"],
                        "method": "unadjusted subgroup mean difference; Welch 95% CI",
                    }
                )
    return pd.DataFrame(rows)


def _single_interaction_test(
    frame: pd.DataFrame,
    feature: str,
    contrast: str,
    treatment_group: str,
    control_group: str,
) -> dict[str, object]:
    subset = frame.loc[frame["segment"].isin([treatment_group, control_group])].copy()
    subset["treatment"] = (subset["segment"] == treatment_group).astype(int)
    if feature == "channel":
        model = smf.ols("spend ~ treatment * C(channel)", data=subset).fit(cov_type="HC3")
        terms = [name for name in model.params.index if "treatment:C(channel)" in name]
        restrictions = np.zeros((len(terms), len(model.params)))
        for row_index, term in enumerate(terms):
            restrictions[row_index, model.params.index.get_loc(term)] = 1
        test = model.wald_test(restrictions, scalar=True)
        return {
            "feature": feature,
            "contrast": contrast,
            "test_type": "joint HC3 Wald test of treatment x channel",
            "df": len(terms),
            "interaction_estimate": np.nan,
            "interaction_ci_low": np.nan,
            "interaction_ci_high": np.nan,
            "statistic": float(test.statistic),
            "p_raw": float(test.pvalue),
        }

    model = smf.ols(f"spend ~ treatment * {feature}", data=subset).fit(cov_type="HC3")
    term = f"treatment:{feature}"
    ci_low, ci_high = model.conf_int().loc[term]
    return {
        "feature": feature,
        "contrast": contrast,
        "test_type": f"HC3 test of treatment x {feature}",
        "df": 1,
        "interaction_estimate": float(model.params[term]),
        "interaction_ci_low": float(ci_low),
        "interaction_ci_high": float(ci_high),
        "statistic": float(model.tvalues[term]),
        "p_raw": float(model.pvalues[term]),
    }


def interaction_tests(frame: pd.DataFrame) -> pd.DataFrame:
    validate_subgroup_features(ALLOWED_SUBGROUP_FEATURES)
    rows = []
    for feature in ["mens", "womens", "newbie", "channel"]:
        for contrast, treatment_group, control_group in PRIMARY_CONTRASTS:
            rows.append(
                _single_interaction_test(
                    frame, feature, contrast, treatment_group, control_group
                )
            )
    result = pd.DataFrame(rows)
    result["p_holm_exploratory_family"] = multipletests(
        result["p_raw"], alpha=0.05, method="holm"
    )[1]
    result["passes_holm_0_05"] = result["p_holm_exploratory_family"] < 0.05
    result.insert(0, "analysis_tier", "exploratory")
    result["family_size"] = len(result)
    return result


def make_subgroup_figure(effects: pd.DataFrame, figures_dir: Path) -> Path:
    figures_dir.mkdir(parents=True, exist_ok=True)
    set_chinese_plot_style(context="notebook")
    fig, axes = plt.subplots(1, 2, figsize=(18, 10), sharex=True, constrained_layout=True)
    for axis, contrast, title in zip(
        axes,
        ["P1", "P2"],
        ["男装邮件 − 不发邮件", "女装邮件 − 不发邮件"],
    ):
        panel = effects.loc[effects["contrast"] == contrast].reset_index(drop=True)
        y = np.arange(len(panel))
        feature_labels = {
            "mens": "历史男装购买",
            "womens": "历史女装购买",
            "newbie": "新客户",
            "channel": "历史渠道",
        }
        level_labels = {0: "否", 1: "是", "Multichannel": "多渠道", "Phone": "电话", "Web": "网页"}
        labels = [
            f"{feature_labels[row.feature]}={level_labels[row.level]} "
            f"(n={row.n_treatment}/{row.n_control})"
            for row in panel.itertuples()
        ]
        values = panel["absolute_effect"].to_numpy()
        axis.errorbar(
            values,
            y,
            xerr=[values - panel["ci_low"].to_numpy(), panel["ci_high"].to_numpy() - values],
            fmt="o",
            capsize=4,
        )
        axis.axvline(0, color="black", linewidth=1)
        axis.set_yticks(y, labels)
        axis.invert_yaxis()
        axis.set_title(title)
        axis.set_xlabel("探索性客均销售额效应（美元）")
    fig.suptitle("实验前子组效应仅用于生成假设，不是定向规则")
    path = figures_dir / "05_subgroup_spend_effects.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def analyze_b5(
    frame: pd.DataFrame, tables_dir: Path, figures_dir: Path
) -> tuple[pd.DataFrame, pd.DataFrame, Path]:
    effects = subgroup_spend_effects(frame)
    interactions = interaction_tests(frame)
    effects.to_csv(tables_dir / "subgroup_spend_effects.csv", index=False)
    interactions.to_csv(tables_dir / "interaction_tests.csv", index=False)
    figure = make_subgroup_figure(effects, figures_dir)
    return effects, interactions, figure

import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from src.analyze_b4 import (
    conversion_mde,
    economic_scenarios,
    validate_covariates,
    winsorized_spend_effects,
)


def test_post_treatment_covariate_is_rejected() -> None:
    with pytest.raises(ValueError, match="post-treatment"):
        validate_covariates({"recency", "conversion"})


def test_unknown_covariate_is_rejected() -> None:
    with pytest.raises(ValueError, match="allowlist"):
        validate_covariates({"recency", "customer_id"})


def test_conversion_mde_reaches_target_power() -> None:
    baseline = 0.006
    n_treatment = 21000
    n_control = 21000
    mde = conversion_mde(n_treatment, n_control, baseline)
    effect_size = proportion_effectsize(baseline + mde, baseline)
    achieved = NormalIndPower().power(effect_size, n_treatment, 0.05, ratio=1.0)
    assert achieved == pytest.approx(0.80, abs=1e-8)
    assert 0 < mde < 0.01


def test_winsorization_uses_one_pooled_cap_without_mutating_input() -> None:
    base = np.linspace(0, 10, 1000)
    frame = pd.DataFrame(
        {
            "segment": np.repeat(["No E-Mail", "Mens E-Mail", "Womens E-Mail"], 1000),
            "spend": np.concatenate([base, base + 1, base + 0.5]),
        }
    )
    frame.loc[[999, 1999, 2999], "spend"] = 1000
    result = winsorized_spend_effects(frame)
    assert len(result) == 3
    assert result["pooled_cap"].nunique() == 1
    assert result["pooled_cap"].iloc[0] < 1000
    assert frame["spend"].max() == 1000


def test_economic_scenario_grid_and_formula() -> None:
    effects = pd.DataFrame(
        {
            "contrast": ["P1", "P2"],
            "metric": ["spend", "spend"],
            "absolute_effect": [1.0, 0.5],
            "ci_low": [0.5, 0.1],
            "ci_high": [1.5, 0.9],
        }
    )
    result = economic_scenarios(effects)
    assert len(result) == 18
    row = result.loc[
        (result["contrast"] == "P1")
        & (result["gross_margin_rate_assumption"] == 0.2)
        & (result["email_cost_per_assigned_assumption"] == 0.1)
    ].iloc[0]
    assert row["incremental_contribution_point"] == pytest.approx(0.1)
    assert row["break_even_spend"] == pytest.approx(0.5)

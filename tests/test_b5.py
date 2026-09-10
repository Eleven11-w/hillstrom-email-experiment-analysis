import pandas as pd
import pytest

from src.analyze_b5 import subgroup_spend_effects, validate_subgroup_features


def test_post_treatment_subgroup_is_rejected() -> None:
    with pytest.raises(ValueError, match="post-treatment"):
        validate_subgroup_features({"mens", "spend"})


def test_unknown_subgroup_is_rejected() -> None:
    with pytest.raises(ValueError, match="allowlist"):
        validate_subgroup_features({"customer_id"})


def test_subgroup_effect_direction_is_treatment_minus_control() -> None:
    frame = pd.DataFrame(
        {
            "segment": ["No E-Mail"] * 4 + ["Mens E-Mail"] * 4 + ["Womens E-Mail"] * 4,
            "mens": [0, 0, 1, 1] * 3,
            "spend": [0.0, 1.0, 1.0, 2.0, 1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 2.0, 3.0],
        }
    )
    result = subgroup_spend_effects(frame, features={"mens"})
    p1 = result.loc[(result["contrast"] == "P1") & (result["level"] == 1)].iloc[0]
    assert p1["absolute_effect"] == 2.0

import pytest
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from src.analyze_b4 import conversion_mde, validate_covariates


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

import numpy as np
import pandas as pd
from scipy import stats

from src.analyze_experiment import bootstrap_group_means, holm_adjust, welch_effect


def test_effect_direction_is_treatment_minus_comparison() -> None:
    treatment = np.array([3.0, 5.0, 7.0])
    comparison = np.array([1.0, 2.0, 3.0])
    result = welch_effect(treatment, comparison)
    assert result["effect"] == 3.0
    var_t = treatment.var(ddof=1) / treatment.size
    var_c = comparison.var(ddof=1) / comparison.size
    manual_se = np.sqrt(var_t + var_c)
    manual_df = (var_t + var_c) ** 2 / (
        var_t**2 / (treatment.size - 1) + var_c**2 / (comparison.size - 1)
    )
    margin = stats.t.ppf(0.975, manual_df) * manual_se
    np.testing.assert_allclose(
        [result["welch_ci_low"], result["welch_ci_high"]],
        [result["effect"] - margin, result["effect"] + margin],
    )


def test_holm_known_values() -> None:
    adjusted = holm_adjust([0.01, 0.04])
    np.testing.assert_allclose(adjusted, [0.02, 0.04])


def test_bootstrap_is_reproducible() -> None:
    frame = pd.DataFrame(
        {
            "segment": ["No E-Mail"] * 3 + ["Mens E-Mail"] * 3 + ["Womens E-Mail"] * 3,
            "spend": [0.0, 1.0, 2.0, 1.0, 2.0, 3.0, 2.0, 3.0, 4.0],
        }
    )
    first = bootstrap_group_means(frame, replicates=20, seed=7, chunk_size=5)
    second = bootstrap_group_means(frame, replicates=20, seed=7, chunk_size=5)
    for group in first:
        np.testing.assert_array_equal(first[group], second[group])

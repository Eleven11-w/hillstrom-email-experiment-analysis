from pathlib import Path

import pandas as pd
import pytest

from src.analyze_experiment import _binary_effect
from src.validate_data import ValidationError, frame_errors, validate_data


def test_small_data_has_expected_proportion_difference() -> None:
    frame = pd.DataFrame(
        {
            "segment": ["No E-Mail"] * 4 + ["Mens E-Mail"] * 4,
            "conversion": [0, 0, 0, 0, 1, 0, 1, 0],
        }
    )
    result = _binary_effect(frame, "conversion", "Mens E-Mail", "No E-Mail")
    assert result["effect"] == 0.5


def test_changed_column_set_fails() -> None:
    frame = pd.DataFrame({"segment": ["No E-Mail"]})
    assert any("column" in error for error in frame_errors(frame))


def test_changed_input_hash_fails(monkeypatch) -> None:
    monkeypatch.setattr("src.validate_data.sha256_file", lambda _: "0" * 64)
    with pytest.raises(ValidationError, match="SHA-256"):
        validate_data(Path("unused.csv"), Path("unused_tables"))

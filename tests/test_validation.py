import pandas as pd

from src.validate_data import EXPECTED_COLUMNS, frame_errors, logic_conflicts


def valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [[1, "1) $0 - $100", 50.0, 1, 0, "Urban", 0, "Web", "No E-Mail", 1, 1, 20.0]],
        columns=EXPECTED_COLUMNS,
    )


def test_illegal_segment_fails() -> None:
    frame = valid_frame()
    frame.loc[0, "segment"] = "Other"
    assert any("segment" in error for error in frame_errors(frame))


def test_nonbinary_outcome_fails() -> None:
    frame = valid_frame()
    frame.loc[0, "visit"] = 2
    assert any("visit" in error for error in frame_errors(frame))


def test_negative_spend_fails() -> None:
    frame = valid_frame()
    frame.loc[0, "spend"] = -1
    assert any("negative" in error for error in frame_errors(frame))


def test_logic_conflict_is_counted() -> None:
    frame = valid_frame()
    frame.loc[0, ["visit", "conversion", "spend"]] = [0, 1, 0]
    conflicts = logic_conflicts(frame)
    assert conflicts["conversion_1_spend_zero"] == 1
    assert conflicts["conversion_1_visit_0"] == 1

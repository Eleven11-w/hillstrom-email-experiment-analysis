from __future__ import annotations

import hashlib
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chisquare


EXPECTED_SHA256 = "0E5893329D8B93CEFECC571777672028290AB69865718020C78C7284F291AECE"
EXPECTED_COLUMNS = [
    "recency",
    "history_segment",
    "history",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
    "segment",
    "visit",
    "conversion",
    "spend",
]
GROUPS = ["No E-Mail", "Mens E-Mail", "Womens E-Mail"]
BINARY_COLUMNS = ["mens", "womens", "newbie", "visit", "conversion"]


class ValidationError(RuntimeError):
    """Raised when a frozen B2 stop rule is triggered."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def frame_errors(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if list(frame.columns) != EXPECTED_COLUMNS:
        return ["schema does not exactly match the frozen column order"]
    if frame.isna().any().any():
        errors.append("required columns contain missing values")
    for column in BINARY_COLUMNS:
        if not set(frame[column].dropna().unique()).issubset({0, 1}):
            errors.append(f"{column} contains values outside 0/1")
    if not set(frame["segment"].dropna().unique()) == set(GROUPS):
        errors.append("segment categories do not match the frozen three arms")
    if not set(frame["zip_code"].dropna().unique()) == {"Rural", "Surburban", "Urban"}:
        errors.append("zip_code categories do not match the source baseline")
    if not set(frame["channel"].dropna().unique()) == {"Multichannel", "Phone", "Web"}:
        errors.append("channel categories do not match the source baseline")
    if not np.isfinite(frame[["recency", "history", "spend"]].to_numpy()).all():
        errors.append("numeric columns contain non-finite values")
    if not frame["recency"].between(1, 12).all() or not np.equal(
        frame["recency"], frame["recency"].astype(int)
    ).all():
        errors.append("recency is not integer-valued within 1..12")
    if (frame[["history", "spend"]] < 0).any().any():
        errors.append("history or spend contains negative values")
    return errors


def logic_conflicts(frame: pd.DataFrame) -> dict[str, int]:
    return {
        "conversion_0_spend_positive": int(
            ((frame["conversion"] == 0) & (frame["spend"] > 0)).sum()
        ),
        "conversion_1_spend_zero": int(
            ((frame["conversion"] == 1) & (frame["spend"] == 0)).sum()
        ),
        "conversion_1_visit_0": int(
            ((frame["conversion"] == 1) & (frame["visit"] == 0)).sum()
        ),
    }


def _pooled_smd(a: pd.Series, b: pd.Series) -> float:
    pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    if pooled == 0:
        return 0.0 if a.mean() == b.mean() else np.inf
    return float((a.mean() - b.mean()) / pooled)


def balance_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for variable in ["recency", "history"]:
        for group_a, group_b in combinations(GROUPS, 2):
            a = frame.loc[frame["segment"] == group_a, variable]
            b = frame.loc[frame["segment"] == group_b, variable]
            smd = _pooled_smd(a, b)
            rows.append(
                {
                    "variable": variable,
                    "kind": "continuous",
                    "level": "",
                    "group_a": group_a,
                    "group_b": group_b,
                    "value_a": a.mean(),
                    "value_b": b.mean(),
                    "difference": a.mean() - b.mean(),
                    "standardized_difference": smd,
                    "review_flag": abs(smd) > 0.10,
                }
            )
    categorical = ["mens", "womens", "newbie", "zip_code", "channel", "history_segment"]
    for variable in categorical:
        levels = sorted(frame[variable].astype(str).unique())
        for level in levels:
            for group_a, group_b in combinations(GROUPS, 2):
                a = (frame.loc[frame["segment"] == group_a, variable].astype(str) == level).mean()
                b = (frame.loc[frame["segment"] == group_b, variable].astype(str) == level).mean()
                difference = float(a - b)
                rows.append(
                    {
                        "variable": variable,
                        "kind": "categorical",
                        "level": level,
                        "group_a": group_a,
                        "group_b": group_b,
                        "value_a": a,
                        "value_b": b,
                        "difference": difference,
                        "standardized_difference": np.nan,
                        "review_flag": abs(difference) > 0.05,
                    }
                )
    return pd.DataFrame(rows)


def validate_data(input_path: Path, tables_dir: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    actual_hash = sha256_file(input_path)
    if actual_hash != EXPECTED_SHA256:
        raise ValidationError(f"input SHA-256 mismatch: {actual_hash}")

    frame = pd.read_csv(input_path)
    errors = frame_errors(frame)
    conflicts = logic_conflicts(frame) if not errors else {}

    qc_rows: list[dict[str, object]] = [
        {"check": "sha256", "value": actual_hash, "status": "pass", "details": "matches frozen input"},
        {"check": "rows", "value": len(frame), "status": "pass" if len(frame) == 64000 else "fail", "details": "expected 64000"},
        {"check": "columns", "value": frame.shape[1], "status": "pass" if frame.shape[1] == 12 else "fail", "details": "expected 12"},
        {"check": "missing_cells", "value": int(frame.isna().sum().sum()), "status": "pass" if not frame.isna().any().any() else "fail", "details": "all required"},
    ]
    for name, count in conflicts.items():
        qc_rows.append(
            {
                "check": name,
                "value": count,
                "status": "pass" if count == 0 else "fail",
                "details": "frozen protocol requires audit if nonzero",
            }
        )
    for error in errors:
        qc_rows.append({"check": "schema_or_value_rule", "value": error, "status": "fail", "details": "B2 stop rule"})
    qc = pd.DataFrame(qc_rows)
    qc.to_csv(tables_dir / "data_qc.csv", index=False)

    if errors:
        raise ValidationError("; ".join(errors))

    observed = frame["segment"].value_counts().reindex(GROUPS)
    expected = np.repeat(len(frame) / 3, 3)
    chi2, srm_p = chisquare(observed.to_numpy(), expected)
    srm = pd.DataFrame(
        {
            "group": GROUPS,
            "observed": observed.to_numpy(),
            "expected": expected,
            "difference": observed.to_numpy() - expected,
            "chi_square": chi2,
            "p_value": srm_p,
            "stop_threshold": 0.01,
            "stop_triggered": srm_p < 0.01,
        }
    )
    srm.to_csv(tables_dir / "srm_check.csv", index=False)

    balance = balance_table(frame)
    balance.to_csv(tables_dir / "balance_check.csv", index=False)

    if len(frame) != 64000 or frame.shape[1] != 12:
        raise ValidationError("row or column count differs from frozen baseline")
    if any(conflicts.values()):
        raise ValidationError("outcome logic conflicts require protocol audit")
    if srm_p < 0.01:
        raise ValidationError(f"SRM stop rule triggered: p={srm_p:.6g}")

    summary = {
        "input_sha256": actual_hash,
        "rows": len(frame),
        "columns": frame.shape[1],
        "srm_chi_square": float(chi2),
        "srm_p_value": float(srm_p),
        "balance_review_flags": int(balance["review_flag"].sum()),
        "max_abs_continuous_smd": float(
            balance.loc[balance["kind"] == "continuous", "standardized_difference"].abs().max()
        ),
        "max_abs_categorical_difference": float(
            balance.loc[balance["kind"] == "categorical", "difference"].abs().max()
        ),
        **conflicts,
    }
    return frame, summary

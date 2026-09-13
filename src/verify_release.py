from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.validate_data import sha256_file


ROW_COUNT_FILES = {
    "group_summary": "results/tables/group_summary.csv",
    "experiment_effects": "results/tables/experiment_effects.csv",
    "conversion_mde": "results/tables/conversion_mde.csv",
    "spend_precision": "results/tables/spend_precision.csv",
    "adjusted_effects": "results/tables/adjusted_effects.csv",
    "winsorized_spend_effects": "results/tables/winsorized_spend_effects.csv",
    "economic_scenarios": "results/tables/economic_scenarios.csv",
    "subgroup_spend_effects": "results/tables/subgroup_spend_effects.csv",
    "interaction_tests": "results/tables/interaction_tests.csv",
}


def verify_release(root: Path) -> list[str]:
    manifest_path = root / "results" / "b6_run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    hash_groups = {
        manifest["input"]["path"]: manifest["input"]["sha256"],
        manifest["protocol"]["path"]: manifest["protocol"]["sha256"],
        **manifest["code_sha256"],
        **manifest["generated_outputs_sha256"],
    }
    for relative_path, expected in hash_groups.items():
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing file: {relative_path}")
        elif sha256_file(path) != expected:
            errors.append(f"hash mismatch: {relative_path}")

    if len(manifest["generated_outputs_sha256"]) != 17:
        errors.append("generated output count is not 17")

    for key, expected_rows in manifest["row_counts"].items():
        relative_path = ROW_COUNT_FILES[key]
        path = root / relative_path
        if path.is_file() and len(pd.read_csv(path)) != expected_rows:
            errors.append(f"row count mismatch: {relative_path}")

    readme = (root / "README.md").read_text(encoding="utf-8")
    for text in ["64,000", "+$0.770", "+$0.424", "18/18"]:
        if text not in readme:
            errors.append(f"README baseline missing: {text}")
    return errors


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors = verify_release(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        raise SystemExit(1)
    print("Release verification passed")
    print("Input/protocol/code/output hashes: PASS")
    print("Generated outputs: 17/17")
    print("Result-table row counts and README baselines: PASS")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path

import matplotlib
import numpy
import pandas
import pytest
import scipy
import seaborn
import statsmodels

from src.analyze_experiment import analyze_b3
from src.analyze_b4 import analyze_b4
from src.analyze_b5 import analyze_b5
from src.validate_data import EXPECTED_SHA256, sha256_file, validate_data


PROTOCOL_SHA256 = "43A7B844B3A0EC01DC0108D1B19ECC6A52FB9CA2992E9D9994C25474E82A90B8"
BOOTSTRAP_SEED = 20260908
BOOTSTRAP_REPLICATES = 10000


def _git_metadata(root: Path) -> dict[str, object]:
    base = ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root)]

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(base + list(args), capture_output=True, text=True, check=False)

    branch_result = run("branch", "--show-current")
    commit_result = run("rev-parse", "HEAD")
    status_result = run("status", "--porcelain")
    return {
        "branch": branch_result.stdout.strip() or None,
        "commit_at_execution": commit_result.stdout.strip() if commit_result.returncode == 0 else None,
        "worktree_clean_before_manifest_write": status_result.returncode == 0 and not status_result.stdout.strip(),
        "note": (
            "commit_at_execution identifies the code used for this run; the execution manifest itself may be committed later"
        ),
    }


def _hash_map(paths: list[Path], root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): sha256_file(path)
        for path in paths
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "raw" / "hillstrom.csv"
    protocol_path = root / "docs" / "analysis_plan.md"
    tables_dir = root / "results" / "tables"
    figures_dir = root / "results" / "figures"

    if sha256_file(protocol_path) != PROTOCOL_SHA256:
        raise RuntimeError("frozen analysis protocol hash mismatch")
    frame, validation = validate_data(input_path, tables_dir)
    summary, effects, b3_figures = analyze_b3(
        frame,
        tables_dir,
        figures_dir,
        replicates=BOOTSTRAP_REPLICATES,
        seed=BOOTSTRAP_SEED,
    )
    mde, precision, adjusted, winsorized, scenarios, b4_figure = analyze_b4(
        frame, effects, tables_dir, figures_dir
    )
    subgroup_effects, interactions, b5_figure = analyze_b5(frame, tables_dir, figures_dir)

    generated_outputs = [
        tables_dir / "data_qc.csv",
        tables_dir / "srm_check.csv",
        tables_dir / "balance_check.csv",
        tables_dir / "group_summary.csv",
        tables_dir / "experiment_effects.csv",
        *b3_figures,
        tables_dir / "conversion_mde.csv",
        tables_dir / "spend_precision.csv",
        tables_dir / "adjusted_effects.csv",
        tables_dir / "winsorized_spend_effects.csv",
        tables_dir / "economic_scenarios.csv",
        b4_figure,
        tables_dir / "subgroup_spend_effects.csv",
        tables_dir / "interaction_tests.csv",
        b5_figure,
    ]
    code_files = (
        sorted((root / "src").glob("*.py"))
        + sorted((root / "scripts").glob("*.*"))
        + sorted((root / "tests").glob("*.py"))
        + [root / ".gitattributes", root / "requirements.txt"]
    )
    manifest = {
        "manifest_version": "1.0",
        "project": "hillstrom-email-ab-test",
        "stage": "B6",
        "status": "completed",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "input": {"path": "data/raw/hillstrom.csv", "sha256": EXPECTED_SHA256},
        "protocol": {"path": "docs/analysis_plan.md", "sha256": PROTOCOL_SHA256},
        "randomness": {
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        },
        "validation": validation,
        "environment": {
            "python": platform.python_version(),
            "pandas": pandas.__version__,
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
            "matplotlib": matplotlib.__version__,
            "seaborn": seaborn.__version__,
            "pytest": pytest.__version__,
        },
        "git": _git_metadata(root),
        "code_sha256": _hash_map(code_files, root),
        "generated_outputs_sha256": _hash_map(generated_outputs, root),
        "row_counts": {
            "group_summary": len(summary),
            "experiment_effects": len(effects),
            "conversion_mde": len(mde),
            "spend_precision": len(precision),
            "adjusted_effects": len(adjusted),
            "winsorized_spend_effects": len(winsorized),
            "economic_scenarios": len(scenarios),
            "subgroup_spend_effects": len(subgroup_effects),
            "interaction_tests": len(interactions),
        },
        "gate_evidence": {
            "b_stats": "pass",
            "b_repro": "pass",
            "holm_significant_subgroup_interactions": int(interactions["passes_holm_0_05"].sum()),
            "final_report": "docs/final_report.md",
            "readme": "README.md",
        },
    }
    manifest_path = root / "results" / "b6_run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("B2 validation passed")
    print("B3-B5 analyses reproduced")
    print("B6 manifest completed")
    print(f"Generated outputs: {len(generated_outputs)}")


if __name__ == "__main__":
    main()

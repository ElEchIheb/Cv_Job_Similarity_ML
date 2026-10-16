"""
tests/test_quality_center.py
AI Quality Center API: every figure comes from a versioned results file, with
its provenance and a status; missing or stale sources are reported as such and
no metric is ever reported for the student's own CV trials.
"""
from __future__ import annotations

import json
import shutil

import pytest

from tests.test_api_extended import auth_headers, client, db_setup  # noqa: F401 — fixtures


@pytest.fixture
def results_dir(tmp_path, monkeypatch):
    """Copy of the real result files in a temporary folder the test can alter."""
    from src.api.routers import ui
    from src.config import settings

    src_dir = settings.PROJECT_ROOT / "evaluation" / "results"
    dst = tmp_path / "results"
    dst.mkdir()
    for name in ("calibration_report.json", "evaluation_results.json", "robustness_probes.json",
                 "functional_trial_fictitious_pdfs.json"):
        shutil.copy(src_dir / name, dst / name)
    monkeypatch.setattr(ui, "_RESULTS_DIR", dst)
    return dst


def _quality(client, headers):  # noqa: F811
    r = client.get("/api/v1/ui/quality", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_quality_reports_shipped_configuration_and_sources(client, auth_headers, results_dir):  # noqa: F811
    from src.decisioning.calibration import load_calibration
    from src.matching.service import MODEL_VERSION

    q = _quality(client, auth_headers)
    assert q["available"] is True
    assert q["shipped"]["model_version"] == MODEL_VERSION
    assert q["shipped"]["calibration_version"] == load_calibration().version
    status = {s["key"]: s["status"] for s in q["sources"]}
    assert status == {"verdicts": "current", "raw": "independent_of_calibration", "robustness": "current",
                      "fictitious_pdfs": "current", "personal_trials": "not_measured"}
    personal = next(s for s in q["sources"] if s["key"] == "personal_trials")
    assert personal["n"] is None and personal["file"] is None


def test_quality_keeps_binary_f1_and_macro_f1_apart(client, auth_headers, results_dir):  # noqa: F811
    report = json.loads((results_dir / "calibration_report.json").read_text(encoding="utf-8"))
    after = report["rows"]["AFTER_product_shipped_calibrated"]
    q = _quality(client, auth_headers)
    shipped = next(r for r in q["verdict_quality"]["rows"] if r["role"] == "shipped")
    assert shipped["macro_f1"] == after["three_class"]["macro_f1"]
    assert shipped["binary_f1"] == after["binary_consider_or_better"]["f1"]
    assert q["verdict_quality"]["confusion"]["matrix"] == after["three_class"]["confusion_matrix_rows_true_cols_pred"]
    # Only final configurations are shown (no pre-calibration row).
    assert {r["role"] for r in q["verdict_quality"]["rows"]} == {"shipped", "comparison"}
    assert q["raw_score"]["n"] == 1800  # test split, not the 12 000-pair dataset
    assert all("binary_f1" in r and "macro_f1" not in r for r in q["raw_score"]["rows"])


def test_quality_flags_stale_and_missing_files(client, auth_headers, results_dir):  # noqa: F811
    probes = json.loads((results_dir / "robustness_probes.json").read_text(encoding="utf-8"))
    probes["calibration_version"] = "older-calibration"
    (results_dir / "robustness_probes.json").write_text(json.dumps(probes), encoding="utf-8")
    (results_dir / "calibration_report.json").unlink()

    q = _quality(client, auth_headers)
    status = {s["key"]: s["status"] for s in q["sources"]}
    assert status["robustness"] == "stale"
    assert status["verdicts"] == "missing"
    assert q["verdict_quality"] is None  # rendered as "not measured", never as zeros


def test_quality_without_any_result_file(client, auth_headers, results_dir):  # noqa: F811
    for f in results_dir.iterdir():
        f.unlink()
    q = _quality(client, auth_headers)
    assert q["available"] is False
    assert q["verdict_quality"] is None and q["raw_score"] is None and q["functional"] is None

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

import src.validator as validator


ROOT = Path(__file__).resolve().parents[1]


def _copy_validation_repo(tmp_path: Path, monkeypatch) -> Path:
    for dirname in ("schema", "legal-corpus", "annotations", "mappings", "examples"):
        shutil.copytree(ROOT / dirname, tmp_path / dirname)
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    return tmp_path


def test_cross_file_validation_catches_article_mismatch(tmp_path: Path, monkeypatch) -> None:
    repo = _copy_validation_repo(tmp_path, monkeypatch)
    traceability = repo / "mappings" / "traceability-matrix.csv"
    text = traceability.read_text(encoding="utf-8")
    traceability.write_text(
        text.replace("CN-AIGC-COMPLAINT-001,CTRL-AIGC-COMPLAINT-MECHANISM,GENAI-2023,生成式人工智能服务管理暂行办法,Interim Measures for the Management of Generative AI Services,第十五条", "CN-AIGC-COMPLAINT-001,CTRL-AIGC-COMPLAINT-MECHANISM,GENAI-2023,生成式人工智能服务管理暂行办法,Interim Measures for the Management of Generative AI Services,第十七条"),
        encoding="utf-8",
    )

    result = validator.validate_cross_file_integrity()

    assert result["valid"] is False
    assert any("article is inconsistent" in error["message"] for error in result["errors"])


def test_source_metadata_validation_catches_missing_source_text(tmp_path: Path, monkeypatch) -> None:
    repo = _copy_validation_repo(tmp_path, monkeypatch)
    example_path = repo / "examples" / "labeling-control.yml"
    example = yaml.safe_load(example_path.read_text(encoding="utf-8"))
    example["source"]["source_text_zh"] = ""
    example_path.write_text(yaml.safe_dump(example, allow_unicode=True, sort_keys=False), encoding="utf-8")

    result = validator.validate_legal_source_metadata()

    assert result["valid"] is False
    assert any("source_text_zh must not be empty" in error["message"] for error in result["errors"])


def test_cross_file_validation_catches_undeclared_expression_field(tmp_path: Path, monkeypatch) -> None:
    repo = _copy_validation_repo(tmp_path, monkeypatch)
    mapping_path = repo / "mappings" / "clause-to-control.yml"
    controls = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    controls[0]["test"]["expression"] = "visible_label_present == true and undeclared_field == true"
    mapping_path.write_text(yaml.safe_dump(controls, allow_unicode=True, sort_keys=False), encoding="utf-8")

    result = validator.validate_cross_file_integrity()

    assert result["valid"] is False
    assert any("undeclared fields" in error["message"] for error in result["errors"])

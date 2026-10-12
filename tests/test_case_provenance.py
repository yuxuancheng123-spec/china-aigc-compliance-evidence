from src.validator import load_yaml, ROOT, validate_validation_case


def _base():
    return {"case_id": "CASE-X", "description": "d", "evidence": {}, "expected": {"CTRL-A": "pass"}}


def test_repository_cases_are_valid():
    for case in load_yaml(ROOT / "examples" / "validation-cases.yml"):
        assert validate_validation_case(case)["valid"], case["case_id"]


def test_inspired_by_requires_disclaimer():
    case = _base()
    case["inspired_by"] = [{"case_name": "A v. B", "court": "C", "date": "2024-06-20",
                            "source_url": "https://example.org", "relation": "adapted_facts"}]
    assert not validate_validation_case(case)["valid"]
    case["disclaimer"] = {"en": "Adapted; not a legal conclusion.", "zh": "改编，不构成法律结论。"}
    assert validate_validation_case(case)["valid"]


def test_relation_must_be_declared():
    case = _base()
    case["inspired_by"] = [{"case_name": "A", "court": "C", "date": "2024", "source_url": "https://example.org"}]
    case["disclaimer"] = {"en": "x", "zh": "y"}
    assert not validate_validation_case(case)["valid"]


def test_grounded_cases_present():
    cases = {c["case_id"]: c for c in load_yaml(ROOT / "examples" / "validation-cases.yml")}
    assert cases["CASE-FAIL-PIPL-BIOMETRIC-REVIEW-REJECTED"]["inspired_by"][0]["relation"] == "adapted_facts"
    assert all(i["relation"] == "extrapolation" for i in cases["CASE-FAIL-DEEPSYN-CONFUSION-LABEL-MISSING"]["inspired_by"])

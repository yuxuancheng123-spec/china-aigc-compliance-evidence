"""End-to-end demo: legal clause -> norm -> control -> evaluation.

Run with ``python -m src.demo`` (or ``make demo``).
"""
from __future__ import annotations

import yaml

from src.evaluator import ROOT, evaluate_control, evaluate_validation_cases, load_controls
from src.validator import validate_repository

DEMO_CASES = [
    "CASE-PASS-METADATA-FIELDS",
    "CASE-FAIL-METADATA-AGGREGATE-ONLY",
    "CASE-REVIEW-LABEL-PROMINENCE",
]
LINE = "-" * 72


def _norm(norm_id: str) -> dict:
    return yaml.safe_load((ROOT / "norms" / f"{norm_id}.yml").read_text(encoding="utf-8"))


def main() -> None:
    print("China AIGC legal-clause-to-control demo\n" + "=" * 72)

    repo = validate_repository()
    flags = ["schema_valid", "cross_file_valid", "legal_source_metadata_fields_complete", "runtime_evidence_schema_valid"]
    ok = all(repo[f] for f in flags)
    print(f"[0] Repository validation: {'OK' if ok else 'ERRORS'} (schemas, cross-file traceability, source metadata, runtime evidence)")

    controls = {c["control_id"]: c for c in load_controls()}
    cases = {c["case_id"]: c for c in yaml.safe_load((ROOT / "examples" / "validation-cases.yml").read_text(encoding="utf-8"))}

    for case_id in DEMO_CASES:
        case = cases[case_id]
        for control_id in case["expected"]:
            control = controls[control_id]
            norm = _norm(control["norm_id"])
            src, n = norm["source"], norm["norm"]
            result = evaluate_control(control, case["evidence"])
            print(LINE)
            print(f"CASE  {case_id}\n      {case['description']}")
            print(f"[1] Clause   {src['document_title_en']} · {src['article']}")
            print(f"             {src['source_text_zh'][:60]}…")
            print(f"[2] Norm     {norm['norm_id']}: {n['regulated_actor']} {n['modality']} {n['action']}")
            print(f"[3] Control  {control_id} ({control['automation_level']})")
            print(f"             test: {control['test']['expression']}")
            print(f"[4] Result   machine={result['machine_result']}  final={result['final_status']}"
                  f"  expected={case['expected'][control_id]}")
            if result.get("review_reason"):
                print(f"             review reason: {result['review_reason']}")

    summary = evaluate_validation_cases()
    print(LINE)
    print(f"All validation cases: {summary['passed']}/{summary['cases_checked']} match expected outcomes")


if __name__ == "__main__":
    main()

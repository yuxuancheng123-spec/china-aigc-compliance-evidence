"""Build the static Norm Explorer from repository data.

Usage: python scripts/build_explorer.py  ->  docs/explorer/index.html
All content is read from norms/, mappings/, examples/ and legal-corpus/,
and example outcomes are computed by src.evaluator at build time.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluator import evaluate_control, load_controls  # noqa: E402

OUT = ROOT / "docs" / "explorer"
TEMPLATE = Path(__file__).with_name("explorer_template.html")
FAVICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#315f82"/>'
    '<text x="16" y="21.5" text-anchor="middle" font-family="Inter, -apple-system, \'Segoe UI\', Arial, sans-serif" '
    'font-size="14" font-weight="600" letter-spacing="-0.5" fill="#fff">YC</text></svg>\n'
)


def build_data() -> dict:
    sources = {}
    with (ROOT / "legal-corpus" / "source-index.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sources[row["source_id"]] = row
    controls = load_controls()
    cases = yaml.safe_load((ROOT / "examples" / "validation-cases.yml").read_text(encoding="utf-8"))

    norms = []
    for path in sorted((ROOT / "norms").glob("*.yml")):
        n = yaml.safe_load(path.read_text(encoding="utf-8"))
        src = n["source"]
        recomputed = hashlib.sha256(src["source_text_zh"].strip().encode("utf-8")).hexdigest()
        stored = src.get("source_snapshot", {}).get("source_excerpt_sha256")
        ctrl_out = []
        for c in [c for c in controls if c["norm_id"] == n["norm_id"]]:
            outcomes = []
            for case in cases:
                if c["control_id"] in case.get("expected", {}):
                    r = evaluate_control(c, case["evidence"])
                    outcomes.append({
                        "case_id": case["case_id"], "description": case["description"],
                        "expected": case["expected"][c["control_id"]],
                        "machine": r["machine_result"], "final": r["final_status"],
                        "review_reason": r.get("review_reason"),
                    })
            ctrl_out.append({
                "control_id": c["control_id"], "component": c.get("control_component"),
                "derivation": c.get("control_derivation_type"), "objective": c["control_objective"],
                "automation_level": c["automation_level"], "automation_profile": c.get("automation_profile", {}),
                "expression": c["test"]["expression"], "required_fields": c["evidence"]["required_fields"],
                "human_review_key": (c.get("required_human_review") or {}).get("review_key"),
                "outcomes": outcomes,
            })
        meta = sources.get(src["source_id"], {})
        norms.append({
            "norm_id": n["norm_id"], "source_id": src["source_id"],
            "title_zh": src["document_title_zh"], "title_en": src["document_title_en"],
            "authority": src.get("issuing_authority"), "article": src["article"],
            "text_zh": src["source_text_zh"], "text_en": src.get("working_translation_en"),
            "url": src.get("source_url"), "effective": src.get("effective_date"),
            "sha256": stored, "sha256_matches": stored == recomputed,
            "verification": src.get("source_snapshot", {}).get("verification_status"),
            "scope_note": meta.get("scope_note"),
            "norm": n["norm"], "interpretation": n["interpretation"], "evidence": n["evidence"],
            "review": n["review"], "controls": ctrl_out,
        })
    return {
        "norms": norms,
        "sources": [{"id": k, "zh": v["document_title_zh"], "en": v["document_title_en"]} for k, v in sources.items()],
        "counts": {"sources": len(sources), "norms": len(norms), "controls": len(controls), "cases": len(cases)},
    }


def main() -> None:
    data = build_data()
    OUT.mkdir(parents=True, exist_ok=True)
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    (OUT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    c = data["counts"]
    print(f"Built {OUT.relative_to(ROOT)}/index.html: {c['norms']} norms, {c['controls']} controls, {c['cases']} cases")


if __name__ == "__main__":
    main()

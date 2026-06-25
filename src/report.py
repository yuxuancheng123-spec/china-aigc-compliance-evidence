from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_markdown_report(bundle: dict, artifacts: dict, template_dir: Path, output_path: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(default_for_string=False, default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("evidence_report.md.j2")
    output_path.write_text(template.render(bundle=bundle, artifacts=artifacts), encoding="utf-8")

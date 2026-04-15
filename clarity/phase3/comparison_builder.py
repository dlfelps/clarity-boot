"""Renders a ComparisonReportData into a self-contained HTML comparison report."""

import os
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .comparison_engine import ComparisonReportData


class ComparisonBuilder:
    """Renders comparison data to an HTML file."""

    def __init__(self) -> None:
        template_dir = Path(__file__).parent / "templates"
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
        )

    def build(self, data: ComparisonReportData, output_dir: str) -> str:
        """Write compare.html to output_dir; return path to the file."""
        os.makedirs(output_dir, exist_ok=True)
        template = self._env.get_template("compare.html.j2")
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        html = template.render(data=data, generated_at=generated_at)

        output_path = os.path.join(output_dir, "compare.html")
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(html)

        return output_path

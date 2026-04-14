"""Renders the ComplexityReportData into an HTML dashboard using Jinja2."""

import os
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .analysis_engine import ComplexityReportData


class ReportBuilder:
    """Renders report data to a self-contained HTML file."""

    def __init__(self) -> None:
        template_dir = Path(__file__).parent / "templates"
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
        )

    def build(self, data: ComplexityReportData, output_dir: str) -> str:
        """Write report/index.html and return its absolute path."""
        template = self._env.get_template("report.html.j2")
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        html = template.render(data=data, generated_at=generated_at)

        output_path = os.path.join(output_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(html)

        return output_path

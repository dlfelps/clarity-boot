"""Clarity Engine CLI — entry point for both phases."""

import os
import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli() -> None:
    """Clarity Engine — a software observatory.

    \b
    clarity init            Phase 1: interactively generate a Gherkin spec
    clarity report <path>   Phase 2: generate a transparency report
    """


@cli.command()
@click.option(
    "--name", "-n",
    default=None,
    help="Feature name; saved to specs/<name>.feature (ignored when --output is given).",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Explicit destination path for the approved Gherkin file.",
)
@click.option(
    "--model", "-m",
    default=None,
    help="Anthropic model to use (default: CLARITY_MODEL env var or claude-sonnet-4-6).",
)
def init(name: str | None, output: str | None, model: str | None) -> None:
    """Phase 1: collaboratively author a Gherkin feature specification."""
    from .phase1.session_manager import InteractiveSessionManager

    resolved_model = model or os.environ.get("CLARITY_MODEL", "claude-sonnet-4-6")

    try:
        InteractiveSessionManager().run(
            feature_name=name,
            output_path=output,
            model=resolved_model,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(str(exc)) from exc


@cli.command()
@click.argument("project_path")
@click.option(
    "--output", "-o",
    default=None,
    help="Report output directory (default: <project_path>/report).",
)
def report(project_path: str, output: str | None) -> None:
    """Phase 2: generate a transparency report for PROJECT_PATH."""
    from .phase2.report_manager import ReportManager

    if output is None:
        output = os.path.join(project_path, "report")

    try:
        path = ReportManager().generate(project_path, output)
        click.echo(f"\n✓ Report generated: {path}")
    except click.ClickException:
        raise
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(str(exc)) from exc

"""Clarity Engine CLI — entry point for both phases."""

import os
import click


@click.group()
def cli() -> None:
    """Clarity Engine — a software observatory.

    \b
    clarity init            Phase 1: interactively generate a Gherkin spec
    clarity report <path>   Phase 2: generate a transparency report
    """


@cli.command()
@click.option(
    "--output", "-o",
    default="approved.feature",
    show_default=True,
    help="Destination path for the approved Gherkin file.",
)
def init(output: str) -> None:
    """Phase 1: collaboratively author a Gherkin feature specification."""
    # Import lazily so the Anthropic SDK is only loaded when this command runs.
    from .phase1.session_manager import InteractiveSessionManager

    try:
        InteractiveSessionManager().run(output_path=output)
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

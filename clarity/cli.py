"""Clarity Engine CLI — entry point for both phases."""

import os
from pathlib import Path
import click
from dotenv import load_dotenv

load_dotenv()


def _ensure_env_file() -> bool:
    """Check that the user has configured their API key.

    If CLAUDE_API_KEY is already present in the environment (set directly or
    loaded from .env by load_dotenv at import time) we proceed without comment.
    If it is absent and no .env file exists in the current directory, we create
    a .env file with placeholder values and print setup instructions, then
    return False so the caller can abort gracefully.

    Returns:
        True if it is safe to proceed, False if the command should abort.
    """
    if os.environ.get("CLAUDE_API_KEY"):
        return True  # key available — nothing to do

    if os.path.exists(".env"):
        return True  # .env exists (key may be inside) — proceed

    # No .env and no key in environment — create .env with placeholders.
    env_src = Path(__file__).parent / "data" / ".env.template"
    env_content = (
        env_src.read_text(encoding="utf-8")
        if env_src.exists()
        else "CLAUDE_API_KEY=your_anthropic_api_key_here\nCLARITY_MODEL=claude-sonnet-4-6\n"
    )
    Path(".env").write_text(env_content, encoding="utf-8")

    click.echo("No .env file found in the current directory.")
    click.echo()
    click.echo("A .env file has been created with placeholder values. To get started:")
    click.echo("  1. Open .env and set CLAUDE_API_KEY to your Anthropic API key")
    click.echo("  2. Re-run: clarity init")
    return False


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
    if not _ensure_env_file():
        return

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

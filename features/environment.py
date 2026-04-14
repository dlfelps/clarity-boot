"""Behave environment hooks for the Clarity Engine test suite."""

import os
import tempfile
import shutil


def before_all(context):
    """Global setup: create a shared temp directory for test artefacts."""
    context.tmp_root = tempfile.mkdtemp(prefix="clarity_test_")


def after_all(context):
    """Global teardown: remove temp artefacts."""
    if hasattr(context, "tmp_root") and os.path.isdir(context.tmp_root):
        shutil.rmtree(context.tmp_root, ignore_errors=True)


def before_scenario(context, scenario):
    """Per-scenario temp dir so tests don't bleed into each other."""
    context.scenario_tmp = tempfile.mkdtemp(dir=context.tmp_root)


def after_scenario(context, scenario):
    if hasattr(context, "scenario_tmp") and os.path.isdir(context.scenario_tmp):
        shutil.rmtree(context.scenario_tmp, ignore_errors=True)

"""Pruebas de rendimiento exigidas por los criterios de exito (SC-004, SC-006)."""

from __future__ import annotations

import time
from pathlib import Path

from typer.testing import CliRunner

from devlog.cli import app

LIST_BUDGET_SECONDS = 3.0
EXPORT_BUDGET_SECONDS = 5.0
NOTE_COUNT = 500


def test_listing_500_notes_completes_within_three_seconds(
    runner: CliRunner, seed_notes
) -> None:
    seed_notes(count=NOTE_COUNT)

    started = time.perf_counter()
    result = runner.invoke(app, ["list"])
    elapsed = time.perf_counter() - started

    assert result.exit_code == 0
    assert elapsed < LIST_BUDGET_SECONDS, f"el listado tardo {elapsed:.2f}s"


def test_exporting_500_notes_keeps_every_note_without_corruption(
    cli_output, runner: CliRunner, seed_notes, tmp_path: Path, monkeypatch
) -> None:
    seed_notes(count=NOTE_COUNT)
    monkeypatch.chdir(tmp_path)

    started = time.perf_counter()
    result = runner.invoke(app, ["export"])
    elapsed = time.perf_counter() - started

    assert result.exit_code == 0
    assert elapsed < EXPORT_BUDGET_SECONDS, f"la exportacion tardo {elapsed:.2f}s"

    document = (tmp_path / "devlog-notes.md").read_text(encoding="utf-8")
    assert document.count("\n## #") == NOTE_COUNT
    assert "contenido" in document

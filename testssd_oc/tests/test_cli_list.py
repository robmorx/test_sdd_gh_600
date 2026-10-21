"""Pruebas del comando `devlog list` (User Story 2)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from devlog.cli import app


def test_list_shows_every_note_newest_first(cli_output, runner: CliRunner, seed_notes) -> None:
    seed_notes(
        specs=[
            ("Antigua", [], "2026-01-01T10:00:00Z"),
            ("Reciente", ["bug"], "2026-01-03T10:00:00Z"),
            ("Media", ["api", "bug"], "2026-01-02T10:00:00Z"),
        ]
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    lines = [line for line in cli_output(result).splitlines() if line.startswith("#")]
    assert len(lines) == 3
    assert "Reciente" in lines[0]
    assert "Media" in lines[1]
    assert "Antigua" in lines[2]
    assert "2026-01-03" in lines[0]
    assert "api, bug" in lines[1]


def test_list_informs_when_there_are_no_notes(cli_output, runner: CliRunner, store_path: Path) -> None:
    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    output = cli_output(result)
    assert "No hay notas guardadas todavía." in output
    assert "Traceback" not in output


def test_list_shows_notes_without_tags(cli_output, runner: CliRunner, seed_notes) -> None:
    seed_notes(specs=[("Sin etiquetas", [], "2026-02-01T10:00:00Z")])

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "(sin etiquetas)" in cli_output(result)


def test_list_shows_all_500_notes_without_omissions_or_duplicates(cli_output, runner: CliRunner, seed_notes) -> None:
    seed_notes(count=500)

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    lines = [line for line in cli_output(result).splitlines() if line.startswith("#")]
    assert len(lines) == 500
    identifiers = {line.split()[0] for line in lines}
    assert len(identifiers) == 500

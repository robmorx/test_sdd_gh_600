"""Pruebas del comando `devlog search` (User Story 3)."""

from __future__ import annotations

from typer.testing import CliRunner

from devlog.cli import app


def test_search_returns_only_notes_with_the_requested_tag(cli_output, runner: CliRunner, seed_notes) -> None:
    seed_notes(
        specs=[
            ("Con bug", ["bug"], "2026-01-03T10:00:00Z"),
            ("Con api", ["api"], "2026-01-02T10:00:00Z"),
            ("Con idea", ["idea"], "2026-01-01T10:00:00Z"),
        ]
    )

    result = runner.invoke(app, ["search", "bug"])

    assert result.exit_code == 0
    output = cli_output(result)
    assert "Con bug" in output
    assert "Con api" not in output
    assert "Con idea" not in output


def test_search_shows_title_date_and_tags_of_each_result(cli_output, runner: CliRunner, seed_notes) -> None:
    seed_notes(specs=[("Con bug", ["bug"], "2026-01-03T10:00:00Z")])

    result = runner.invoke(app, ["search", "bug"])

    assert result.exit_code == 0
    line = next(line for line in cli_output(result).splitlines() if line.startswith("#"))
    assert "Con bug" in line
    assert "2026-01-03" in line
    assert "bug" in line


def test_search_requires_every_requested_tag(cli_output, runner: CliRunner, seed_notes) -> None:
    seed_notes(
        specs=[
            ("Bug y api", ["bug", "api"], "2026-01-02T10:00:00Z"),
            ("Solo bug", ["bug"], "2026-01-01T10:00:00Z"),
        ]
    )

    result = runner.invoke(app, ["search", "bug", "api"])

    assert result.exit_code == 0
    output = cli_output(result)
    assert "Bug y api" in output
    assert "Solo bug" not in output


def test_search_normalizes_the_requested_tag(cli_output, runner: CliRunner, seed_notes) -> None:
    seed_notes(specs=[("Con bug", ["bug"], "2026-01-01T10:00:00Z")])

    result = runner.invoke(app, ["search", " BUG "])

    assert result.exit_code == 0
    assert "Con bug" in cli_output(result)


def test_search_reports_no_matches_with_exit_code_three(cli_output, runner: CliRunner, seed_notes) -> None:
    seed_notes(specs=[("Con bug", ["bug"], "2026-01-01T10:00:00Z")])

    result = runner.invoke(app, ["search", "desconocida"])

    assert result.exit_code == 3
    assert "No se encontraron notas con esas etiquetas." in cli_output(result)


def test_search_without_tags_is_a_usage_error(cli_output, runner: CliRunner, store_path) -> None:
    result = runner.invoke(app, ["search"])

    assert result.exit_code == 2

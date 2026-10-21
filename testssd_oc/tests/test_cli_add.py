"""Pruebas del comando `devlog add` (User Story 1)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from devlog import db, repository
from devlog.cli import app


def test_add_creates_a_note_with_title_content_and_tags(cli_output, runner: CliRunner, store_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "add",
            "CORS error in staging",
            "--content",
            "El servidor rechaza el preflight OPTIONS.",
            "--tag",
            "bug",
            "--tag",
            "api",
        ],
    )

    assert result.exit_code == 0
    output = cli_output(result)
    assert "Nota #1 guardada (" in output
    assert "Etiquetas: bug, api" in output

    with db.open_store(store_path) as connection:
        stored = repository.list_notes(connection)

    assert len(stored) == 1
    assert stored[0].title == "CORS error in staging"
    assert stored[0].content == "El servidor rechaza el preflight OPTIONS."
    assert stored[0].tags == ("api", "bug")


def test_add_accepts_a_title_only_note(cli_output, runner: CliRunner, store_path: Path) -> None:
    result = runner.invoke(app, ["add", "Solo titulo"])

    assert result.exit_code == 0
    output = cli_output(result)
    assert "Nota #1 guardada (" in output
    assert "Etiquetas:" not in output

    with db.open_store(store_path) as connection:
        stored = repository.list_notes(connection)

    assert stored[0].content == ""
    assert stored[0].tags == ()


def test_add_persists_the_note_across_invocations(cli_output, runner: CliRunner, store_path: Path) -> None:
    first = runner.invoke(app, ["add", "Persistente"])
    second = runner.invoke(app, ["add", "Segunda"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "Nota #2 guardada" in cli_output(second)

    with db.open_store(store_path) as connection:
        stored = repository.list_notes(connection)

    assert {note.title for note in stored} == {"Persistente", "Segunda"}


def test_add_rejects_an_empty_title(cli_output, runner: CliRunner, store_path: Path) -> None:
    result = runner.invoke(app, ["add", "   "])

    assert result.exit_code == 2
    assert "El título no puede estar vacío." in cli_output(result)

    with db.open_store(store_path) as connection:
        assert repository.count_notes(connection) == 0


def test_add_requires_a_title(cli_output, runner: CliRunner, store_path: Path) -> None:
    result = runner.invoke(app, ["add"])

    assert result.exit_code == 2

    with db.open_store(store_path) as connection:
        assert repository.count_notes(connection) == 0


def test_add_reads_multi_line_content_from_stdin(cli_output, runner: CliRunner, store_path: Path) -> None:
    result = runner.invoke(app, ["add", "Desde stdin", "--content-file", "-"], input="linea 1\nlinea 2\n")

    assert result.exit_code == 0

    with db.open_store(store_path) as connection:
        stored = repository.list_notes(connection)

    assert stored[0].content == "linea 1\nlinea 2\n"


def test_add_reads_content_from_a_file(cli_output, runner: CliRunner, store_path: Path, tmp_path: Path) -> None:
    source = tmp_path / "cuerpo.md"
    source.write_text("- uno\n- dos\n", encoding="utf-8")

    result = runner.invoke(app, ["add", "Desde archivo", "--content-file", str(source)])

    assert result.exit_code == 0

    with db.open_store(store_path) as connection:
        stored = repository.list_notes(connection)

    assert stored[0].content == "- uno\n- dos\n"


def test_add_normalizes_tags_and_drops_duplicates(cli_output, runner: CliRunner, store_path: Path) -> None:
    result = runner.invoke(app, ["add", "Etiquetas", "--tag", " Bug ", "--tag", "bug", "--tag", "API"])

    assert result.exit_code == 0
    assert "Etiquetas: bug, api" in cli_output(result)

    with db.open_store(store_path) as connection:
        stored = repository.list_notes(connection)

    assert stored[0].tags == ("api", "bug")


def test_add_reports_a_corrupted_store_without_touching_it(cli_output, 
    runner: CliRunner, tmp_path: Path, monkeypatch
) -> None:
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"esto no es una base de datos")
    before = corrupt.read_bytes()
    monkeypatch.setenv("DEVLOG_DB_PATH", str(corrupt))

    result = runner.invoke(app, ["add", "Con almacen roto"])

    assert result.exit_code == 1
    output = cli_output(result)
    assert "No se pudo abrir la base de datos" in output
    assert "Traceback" not in output
    assert corrupt.read_bytes() == before

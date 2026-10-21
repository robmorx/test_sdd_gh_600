"""Pruebas del comando `devlog export` (User Story 4)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from devlog.cli import app


def test_export_creates_a_markdown_file_with_every_note(
    cli_output, runner: CliRunner, seed_notes, tmp_path: Path, monkeypatch
) -> None:
    seed_notes(
        specs=[
            ("CORS error in staging", ["api", "bug"], "2026-10-21T09:30:00Z"),
            ("Useful psql snippet", [], "2026-10-20T18:05:00Z"),
        ]
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["export"])

    assert result.exit_code == 0
    output = cli_output(result)
    assert "Notas exportadas a devlog-notes.md (2 notas)." in output

    document = (tmp_path / "devlog-notes.md").read_text(encoding="utf-8")
    assert "# Notas de DevLog" in document
    assert "## #1 · CORS error in staging" in document
    assert "## #2 · Useful psql snippet" in document
    assert "- **Etiquetas**: `api`, `bug`" in document
    assert "- **Etiquetas**: (sin etiquetas)" in document


def test_export_preserves_the_content_of_every_note(
    cli_output, runner: CliRunner, seed_notes, tmp_path: Path, monkeypatch
) -> None:
    body = "- uno\n- dos\n\n\"comillas\" y \\barra"
    seed_notes(specs=[("Con cuerpo", [], "2026-10-21T09:30:00Z", body)])
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["export"])

    assert result.exit_code == 0
    document = (tmp_path / "devlog-notes.md").read_text(encoding="utf-8")
    assert body in document


def test_export_honours_the_output_option(cli_output, runner: CliRunner, seed_notes, tmp_path: Path) -> None:
    seed_notes(specs=[("Una", [], "2026-10-21T09:30:00Z")])
    destination = tmp_path / "salida" / "notas.md"
    destination.parent.mkdir()

    result = runner.invoke(app, ["export", "--output", str(destination)])

    assert result.exit_code == 0
    assert destination.exists()


def test_export_asks_before_overwriting_an_existing_file(
    cli_output, runner: CliRunner, seed_notes, tmp_path: Path, monkeypatch
) -> None:
    seed_notes(specs=[("Una", [], "2026-10-21T09:30:00Z")])
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / "devlog-notes.md"
    destination.write_text("contenido previo", encoding="utf-8")
    monkeypatch.setattr("devlog.cli.stdin_is_interactive", lambda: True)

    result = runner.invoke(app, ["export"], input="n\n")

    assert result.exit_code == 1
    assert destination.read_text(encoding="utf-8") == "contenido previo"
    assert "No se sobrescribió el archivo." in cli_output(result)


def test_export_overwrites_when_the_user_confirms(
    cli_output, runner: CliRunner, seed_notes, tmp_path: Path, monkeypatch
) -> None:
    seed_notes(specs=[("Una", [], "2026-10-21T09:30:00Z")])
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / "devlog-notes.md"
    destination.write_text("contenido previo", encoding="utf-8")
    monkeypatch.setattr("devlog.cli.stdin_is_interactive", lambda: True)

    result = runner.invoke(app, ["export"], input="s\n")

    assert result.exit_code == 0
    assert "contenido previo" not in destination.read_text(encoding="utf-8")
    assert "# Notas de DevLog" in destination.read_text(encoding="utf-8")


def test_export_with_force_replaces_without_asking(
    cli_output, runner: CliRunner, seed_notes, tmp_path: Path, monkeypatch
) -> None:
    seed_notes(specs=[("Una", [], "2026-10-21T09:30:00Z")])
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / "devlog-notes.md"
    destination.write_text("contenido previo", encoding="utf-8")
    monkeypatch.setattr("devlog.cli.stdin_is_interactive", lambda: False)

    result = runner.invoke(app, ["export", "--force"])

    assert result.exit_code == 0
    assert "# Notas de DevLog" in destination.read_text(encoding="utf-8")


def test_export_refuses_to_overwrite_in_a_non_interactive_session(
    cli_output, runner: CliRunner, seed_notes, tmp_path: Path, monkeypatch
) -> None:
    seed_notes(specs=[("Una", [], "2026-10-21T09:30:00Z")])
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / "devlog-notes.md"
    destination.write_text("contenido previo", encoding="utf-8")
    monkeypatch.setattr("devlog.cli.stdin_is_interactive", lambda: False)

    result = runner.invoke(app, ["export"])

    assert result.exit_code == 1
    assert destination.read_text(encoding="utf-8") == "contenido previo"
    assert "Usa --force o indica otra ruta con --output." in cli_output(result)


def test_export_reports_a_missing_destination_directory(
    cli_output, runner: CliRunner, store_path: Path, tmp_path: Path
) -> None:
    destination = tmp_path / "no-existe" / "notas.md"

    result = runner.invoke(app, ["export", "--output", str(destination)])

    assert result.exit_code == 1
    assert "No existe el directorio de destino:" in cli_output(result)
    assert not destination.exists()
    assert list(tmp_path.glob("**/*.tmp")) == []


def test_export_with_no_notes_creates_a_valid_empty_file(
    cli_output, runner: CliRunner, store_path: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["export"])

    assert result.exit_code == 0
    assert "No había notas para exportar." in cli_output(result)
    document = (tmp_path / "devlog-notes.md").read_text(encoding="utf-8")
    assert document.startswith("# Notas de DevLog")
    assert "0 notas" in document

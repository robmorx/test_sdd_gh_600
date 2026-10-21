"""Interfaz de linea de comandos de DevLog.

Los cuatro comandos del alcance v1 son ``add``, ``list``, ``search`` y ``export``.
Todos los mensajes visibles estan en espanol, sin trazas tecnicas (FR-020), y cada
operacion devuelve el codigo de salida definido en `contracts/cli.md`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from devlog import config
from devlog.errors import DevLogError
from devlog.formatting import format_local_datetime, format_note_line
from devlog.services import export_service, note_service, search_service

app = typer.Typer(
    name="devlog",
    help="DevLog CLI: guarda notas de desarrollo en SQLite y exportalas a Markdown.",
    add_completion=False,
    no_args_is_help=True,
)


def stdin_is_interactive() -> bool:
    """Indica si la entrada estandar es interactiva (una terminal)."""
    try:
        return bool(sys.stdin is not None and sys.stdin.isatty())
    except (AttributeError, ValueError):  # pragma: no cover -entrada estandar unusual
        return False


def _fail(error: DevLogError) -> None:
    """Muestra el error al usuario y termina con su codigo de salida."""
    typer.echo(error.message, err=True)
    raise typer.Exit(code=error.exit_code)


def _read_content(
    content: Optional[str],
    content_file: Optional[Path],
) -> str:
    """Resuelve el cuerpo de la nota segun el origen indicado por el usuario."""
    if content_file is not None:
        if str(content_file) == "-":
            return sys.stdin.read()
        try:
            return content_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise typer.BadParameter(
                f"No se pudo leer el archivo de contenido: {content_file}."
            ) from exc
    if content is not None:
        return content
    if not stdin_is_interactive():
        return sys.stdin.read()
    return ""


def _confirm_overwrite(path: Path) -> bool:
    """Pide confirmacion al usuario antes de sobrescribir un archivo existente.

    Acepta ``s``, ``si``, ``y`` y ``yes``; cualquier otra respuesta (o el fin de la
    entrada) significa que no.
    """
    typer.echo(f"El archivo ya existe: {path}. ¿Quieres sobrescribirlo? [s/N]")
    answer = (sys.stdin.readline() or "").strip().lower()
    return answer in {"s", "si", "sí", "y", "yes"}


@app.command("add")
def add_note(
    title: Annotated[
        Optional[str],
        typer.Argument(help="Titulo de la nota (obligatorio)."),
    ] = None,
    title_option: Annotated[
        Optional[str],
        typer.Option("--title", help="Titulo de la nota, como alternativa al argumento."),
    ] = None,
    tags: Annotated[
        Optional[list[str]],
        typer.Option("--tag", "-t", help="Etiqueta de la nota; se puede repetir."),
    ] = None,
    content: Annotated[
        Optional[str],
        typer.Option("--content", "-c", help="Contenido de la nota."),
    ] = None,
    content_file: Annotated[
        Optional[Path],
        typer.Option(
            "--content-file",
            help="Archivo con el contenido; usa '-' para leer la entrada estandar.",
        ),
    ] = None,
) -> None:
    """Crea una nota con titulo, contenido opcional y etiquetas."""
    if title is not None and title_option is not None:
        raise typer.BadParameter(
            "Indica el titulo una sola vez: como argumento o con --title, no ambos."
        )
    final_title = title if title is not None else title_option
    if final_title is None:
        raise typer.BadParameter("Falta el titulo de la nota.")

    body = _read_content(content, content_file)

    try:
        note = note_service.create_note(final_title, body, list(tags or []))
    except DevLogError as error:
        _fail(error)
        return

    typer.echo(f"Nota #{note.id} guardada ({format_local_datetime(note.created_at)}).")
    if note.tags:
        typer.echo(f"Etiquetas: {', '.join(note.tags)}")


@app.command("list")
def list_notes_command() -> None:
    """Muestra todas las notas guardadas, de la mas nueva a la mas antigua."""
    try:
        notes = note_service.list_notes()
    except DevLogError as error:
        _fail(error)
        return

    if not notes:
        typer.echo("No hay notas guardadas todavía.")
        return

    for note in notes:
        typer.echo(format_note_line(note))


@app.command("search")
def search_notes_command(
    tags: Annotated[
        list[str],
        typer.Argument(help="Etiqueta a buscar; se puede repetir."),
    ] = [],
) -> None:
    """Busca notas por etiqueta; con varias etiquetas exige todas (AND)."""
    try:
        results = search_service.search_by_tags(list(tags))
    except DevLogError as error:
        _fail(error)
        return

    if not results:
        typer.echo("No se encontraron notas con esas etiquetas.")
        raise typer.Exit(code=config.EXIT_NO_RESULTS)

    for note in results:
        typer.echo(format_note_line(note))


@app.command("export")
def export_notes_command(
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Ruta del archivo Markdown de destino."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Sobrescribe el archivo sin pedir confirmacion."),
    ] = False,
) -> None:
    """Exporta todas las notas a un archivo Markdown."""
    destination = config.resolve_export_path(output)

    confirm = None
    if destination.exists() and not force and stdin_is_interactive():
        def confirm(path: Path) -> bool:  # noqa: F811 -confirmacion local
            return _confirm_overwrite(path)

    try:
        result = export_service.export_notes(destination, force=force, confirm=confirm)
    except DevLogError as error:
        _fail(error)
        return

    if result.note_count == 0:
        typer.echo("No había notas para exportar.")
        return

    typer.echo(f"Notas exportadas a {result.path} ({result.note_count} notas).")

"""Servicio de exportacion a Markdown (User Story 4)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable

from devlog.errors import ExportPathError
from devlog.formatting import utc_now_iso
from devlog.markdown import render_document
from devlog.models import ExportResult
from devlog.services.note_service import list_notes

ConfirmCallback = Callable[[Path], bool]

EXISTING_FILE_MESSAGE = (
    "El archivo ya existe y no se puede pedir confirmación. "
    "Usa --force o indica otra ruta con --output."
)
CANCELLED_MESSAGE = "No se sobrescribió el archivo."


def _write_atomically(path: Path, document: str) -> None:
    """Escribe el documento y lo mueve a su destino final.

    Si algo falla, el archivo temporal se borra y no queda ningun archivo parcial
    (caso limite del spec: destino invalido).
    """
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=".devlog-export-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(document)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def export_notes(
    destination: Path,
    force: bool = False,
    confirm: ConfirmCallback | None = None,
) -> ExportResult:
    """Exporta todas las notas a un archivo Markdown.

    Nunca se sobrescribe un archivo existente sin confirmacion explicita en ese
    momento: un prompt de confirmacion o el flag ``--force`` (FR-015). En una sesion no
    interactiva sin ``--force`` la operacion se rechaza y el archivo se queda intacto.
    """
    path = Path(destination)

    if path.exists() and not force:
        if confirm is None:
            raise ExportPathError(EXISTING_FILE_MESSAGE)
        if not confirm(path):
            raise ExportPathError(CANCELLED_MESSAGE)

    parent = path.parent if str(path.parent) else Path(".")
    if not parent.exists():
        raise ExportPathError(f"No existe el directorio de destino: {parent}.")
    if not os.access(parent, os.W_OK):
        raise ExportPathError(f"No se pudo escribir el archivo: {path}.")

    notes = list_notes()
    generated_at = utc_now_iso()
    document = render_document(notes, generated_at)

    try:
        _write_atomically(path, document)
    except OSError as exc:
        raise ExportPathError(f"No se pudo escribir el archivo: {path}.") from exc

    return ExportResult(path=str(path), note_count=len(notes), generated_at=generated_at)

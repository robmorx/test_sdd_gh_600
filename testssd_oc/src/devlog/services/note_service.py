"""Servicio de creacion y consulta de notas (User Stories 1 y 2)."""

from __future__ import annotations

from devlog import config, db, repository
from devlog.errors import ValidationError
from devlog.formatting import split_tags
from devlog.models import Note

EMPTY_TITLE_MESSAGE = "El título no puede estar vacío."


def create_note(title: str, content: str, tags: list[str] | None = None) -> Note:
    """Crea una nota con titulo obligatorio, contenido opcional y etiquetas normalizadas.

    El titulo no puede estar vacio ni contener solo espacios (FR-016). Las etiquetas se
    recortan, se pasan a minusculas y se eliminan las repetidas (FR-017).
    """
    clean_title = (title or "").strip()
    if not clean_title:
        raise ValidationError(EMPTY_TITLE_MESSAGE)

    normalized_tags = split_tags(tags or [])
    with db.open_store(config.resolve_store_path()) as connection:
        return repository.insert_note(connection, clean_title, content or "", normalized_tags)


def list_notes() -> list[Note]:
    """Devuelve todas las notas, de la mas nueva a la mas antigua (FR-007)."""
    with db.open_store(config.resolve_store_path()) as connection:
        return repository.list_notes(connection)

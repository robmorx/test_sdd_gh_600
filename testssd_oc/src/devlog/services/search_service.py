"""Servicio de busqueda por etiquetas (User Story 3)."""

from __future__ import annotations

from devlog import config, db, repository
from devlog.errors import ValidationError
from devlog.formatting import split_tags
from devlog.models import Note

NO_TAGS_MESSAGE = "Debes indicar al menos una etiqueta para buscar."


def search_by_tags(tags: list[str] | None) -> list[Note]:
    """Busca las notas que carry **todas** las etiquetas indicadas.

    La coincidencia es exacta sobre el valor normalizado de la etiqueta (FR-010).
    """
    normalized_tags = split_tags(tags or [])
    if not normalized_tags:
        raise ValidationError(NO_TAGS_MESSAGE)

    with db.open_store(config.resolve_store_path()) as connection:
        return repository.search_notes_by_tags(connection, normalized_tags)

"""Normalizacion y presentacion de datos (etiquetas, fechas y lineas de listado)."""

from __future__ import annotations

from datetime import datetime, timezone

from devlog.models import Note

NO_TAGS_LABEL = "(sin etiquetas)"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def normalize_tag(name: str) -> str:
    """Normaliza una etiqueta: recorta espacios y unifica las mayusculas (FR-017)."""
    return name.strip().lower()


def split_tags(values: list[str] | tuple[str, ...] | None) -> list[str]:
    """Normaliza una lista de etiquetas, separando valores por coma y quitando duplicados."""
    normalized: list[str] = []
    for raw in values or ():
        for part in str(raw).split(","):
            tag = normalize_tag(part)
            if tag and tag not in normalized:
                normalized.append(tag)
    return normalized


def utc_now_iso() -> str:
    """Devuelve la hora actual en ISO-8601 UTC con precision de segundos."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_local_datetime(iso_utc: str) -> str:
    """Convierte una marca de tiempo UTC al formato local legible ``YYYY-MM-DD HH:MM``."""
    moment = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    return moment.astimezone().strftime(DATETIME_FORMAT)


def format_tag_list(tags: tuple[str, ...] | list[str]) -> str:
    """Presenta las etiquetas de una nota; `(sin etiquetas)` cuando no tiene ninguna."""
    if not tags:
        return NO_TAGS_LABEL
    return ", ".join(tags)


def format_note_line(note: Note) -> str:
    """Construye la linea de listado de una nota.

    Formato: ``#<id>  <fecha>  <etiquetas>  <titulo>``. El titulo va al final para que
    nunca se trunque, y la linea es texto plano para que sea estable y verificable.
    """
    created = format_local_datetime(note.created_at)
    return f"#{note.id}  {created}  {format_tag_list(note.tags)}  {note.title}"

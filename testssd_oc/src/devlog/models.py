"""Entidades del dominio DevLog (ver `data-model.md`)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Note:
    """Nota de desarrollo.

    ``title`` es obligatorio y no puede estar vacio ni contener solo espacios.
    ``content`` es opcional y se conserva tal cual, incluidos los saltos de linea.
    ``created_at`` es una marca de tiempo UTC inmutable.
    """

    id: int
    title: str
    content: str
    created_at: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Tag:
    """Etiqueta normalizada (recortada y en minusculas) compartida entre notas."""

    id: int
    name: str
    created_at: str


@dataclass(frozen=True)
class ExportResult:
    """Resultado derivado de una exportacion; no es un registro almacenado."""

    path: str
    note_count: int
    generated_at: str

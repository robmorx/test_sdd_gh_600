"""Generacion del documento Markdown exportado (ver `contracts/markdown-export.md`).

La regla central es que el **cuerpo de la nota se escribe tal cual**: los saltos de
linea, las listas y los caracteres especiales se conservan byte a byte (FR-018, SC-006).
Solo se aplican dos transformaciones controladas:

* el titulo se escapa para que no pueda romper la estructura del documento;
* un cuerpo que contenga una linea de tres o mas acentos graves se envuelve en un
  cerco mas largo para que no pueda cerrarse antes de tiempo.
"""

from __future__ import annotations

import re

from devlog.formatting import format_local_datetime
from devlog.models import Note

DOCUMENT_TITLE = "# Notas de DevLog"

#: Caracteres que se escapan siempre en el titulo.
TITLE_ESCAPE_CHARS = "\\`*_[]#<>!|"

#: Caracteres que se escapan solo al inicio del titulo (markdown de bloque).
TITLE_LEADING_ESCAPE_CHARS = "-+."

_FENCE_RUN = re.compile(r"^`{3,}", re.MULTILINE)


def escape_title(title: str) -> str:
    """Escapa el titulo de una nota para que no altere la estructura del documento."""
    escaped: list[str] = []
    for index, char in enumerate(title):
        if char in TITLE_ESCAPE_CHARS or (index == 0 and char in TITLE_LEADING_ESCAPE_CHARS):
            escaped.append("\\" + char)
        else:
            escaped.append(char)
    return "".join(escaped)


def fence_body(body: str) -> str:
    """Envuelve el cuerpo en un cerco solo si contiene una linea de 3+ acentos graves."""
    runs = [len(match.group(0)) for match in _FENCE_RUN.finditer(body)]
    longest = max(runs) if runs else 0
    if longest < 3:
        return body
    fence = "`" * max(3, longest + 1)
    suffix = "" if body.endswith("\n") else "\n"
    return f"{fence}\n{body}{suffix}{fence}"


def _format_tag_metadata(tags: tuple[str, ...]) -> str:
    """Formatea la linea de etiquetas del documento exportado."""
    if not tags:
        return "(sin etiquetas)"
    return ", ".join(f"`{tag}`" for tag in sorted(tags))


def render_document(notes: list[Note], generated_at: str) -> str:
    """Construye el documento Markdown completo con todas las notas."""
    count = len(notes)
    plural = "nota" if count == 1 else "notas"
    stamp = format_local_datetime(generated_at)

    lines: list[str] = [
        DOCUMENT_TITLE,
        "",
        f"{stamp} · {count} {plural}",
        "",
        "---",
        "",
    ]

    for index, note in enumerate(notes):
        if index > 0:
            lines.extend(["---", ""])
        lines.append(f"## #{note.id} · {escape_title(note.title)}")
        lines.append("")
        lines.append(f"- **Creado**: {format_local_datetime(note.created_at)}")
        lines.append(f"- **Etiquetas**: {_format_tag_metadata(note.tags)}")
        lines.append("")
        lines.append(fence_body(note.content))
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"

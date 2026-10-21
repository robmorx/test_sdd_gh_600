"""Acceso a datos: unicamente SQL parametrizado sobre el almacen de DevLog.

Reglas implementadas aqui:

* las etiquetas se comparan **exactamente** contra su valor normalizado y, cuando se
  pide mas de una, la nota debe tener **todas** (semantica AND) (FR-010, research.md R2);
* el orden de lectura es del mas nuevo al mas viejo, con el id como desempate para que
  dos notas del mismo segundo tengan un orden determinista (FR-007, research.md R7);
* el par ``(note_id, tag_id)`` es clave primaria, de modo que una etiqueta repetida
  dentro de la misma nota es imposible (FR-017, research.md R12).
"""

from __future__ import annotations

import sqlite3

from devlog.formatting import normalize_tag, utc_now_iso
from devlog.models import Note

_TAG_NAMES_SUBQUERY = (
    "(SELECT COALESCE(GROUP_CONCAT(t2.name, ','), '') "
    "FROM note_tags nt2 JOIN tags t2 ON t2.id = nt2.tag_id "
    "WHERE nt2.note_id = n.id)"
)


def _row_to_note(row: sqlite3.Row) -> Note:
    """Convierte una fila de consulta en una :class:`Note`."""
    raw_tags = row["tag_names"] or ""
    tags = tuple(sorted(tag for tag in raw_tags.split(",") if tag))
    return Note(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        created_at=row["created_at"],
        tags=tags,
    )


def insert_note(
    connection: sqlite3.Connection,
    title: str,
    content: str,
    tags: list[str],
    created_at: str | None = None,
) -> Note:
    """Inserta una nota y sus etiquetas en una unica transaccion.

    Las etiquetas se normalizan aqui (recortadas, en minusculas y sin repetir) para que
    la invariante "una etiqueta una sola vez por nota" se cumpla aunque el llamante no
    la haya normalizado (FR-017).
    """
    created = created_at or utc_now_iso()
    normalized_tags: list[str] = []
    for tag in tags:
        clean = normalize_tag(tag)
        if clean and clean not in normalized_tags:
            normalized_tags.append(clean)

    with connection:
        cursor = connection.execute(
            "INSERT INTO notes (title, content, created_at) VALUES (?, ?, ?)",
            (title, content, created),
        )
        note_id = int(cursor.lastrowid)
        for tag in normalized_tags:
            connection.execute(
                "INSERT OR IGNORE INTO tags (name, created_at) VALUES (?, ?)",
                (tag, created),
            )
            tag_row = connection.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()
            connection.execute(
                "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                (note_id, int(tag_row["id"])),
            )
    return Note(
        id=note_id,
        title=title,
        content=content,
        created_at=created,
        tags=tuple(normalized_tags),
    )


def list_notes(connection: sqlite3.Connection) -> list[Note]:
    """Devuelve todas las notas, de la mas nueva a la mas antigua."""
    rows = connection.execute(
        f"SELECT n.id, n.title, n.content, n.created_at, {_TAG_NAMES_SUBQUERY} AS tag_names "
        "FROM notes n ORDER BY n.created_at DESC, n.id DESC"
    ).fetchall()
    return [_row_to_note(row) for row in rows]


def search_notes_by_tags(connection: sqlite3.Connection, tags: list[str]) -> list[Note]:
    """Devuelve las notas que tienen **todas** las etiquetas indicadas."""
    if not tags:
        return []
    placeholders = ", ".join("?" for _ in tags)
    rows = connection.execute(
        f"SELECT n.id, n.title, n.content, n.created_at, {_TAG_NAMES_SUBQUERY} AS tag_names "
        "FROM notes n WHERE n.id IN ("
        "  SELECT nt.note_id FROM note_tags nt JOIN tags t ON t.id = nt.tag_id"
        f"  WHERE t.name IN ({placeholders})"
        "  GROUP BY nt.note_id HAVING COUNT(DISTINCT t.name) = ?"
        ") ORDER BY n.created_at DESC, n.id DESC",
        (*tags, len(tags)),
    ).fetchall()
    return [_row_to_note(row) for row in rows]


def count_notes(connection: sqlite3.Connection) -> int:
    """Devuelve el numero total de notas almacenadas."""
    row = connection.execute("SELECT COUNT(*) AS total FROM notes").fetchone()
    return int(row["total"])


def get_tags_for_note(connection: sqlite3.Connection, note_id: int) -> list[str]:
    """Devuelve las etiquetas de una nota, ordenadas alfabeticamente."""
    rows = connection.execute(
        "SELECT t.name FROM tags t JOIN note_tags nt ON nt.tag_id = t.id "
        "WHERE nt.note_id = ? ORDER BY t.name",
        (note_id,),
    ).fetchall()
    return [str(row["name"]) for row in rows]

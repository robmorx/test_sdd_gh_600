"""Acceso al almacen SQLite de DevLog.

Reglas invariables de este modulo (Constitution Principle II, FR-019):

* la unica operacion de esquema permitida es ``CREATE ... IF NOT EXISTS``;
* no existe ninguna funcion que borre, reinicie o recree el almacen;
* un almacen existente se comprueba **en modo solo lectura** antes de abrirlo, de modo
  que un archivo danado nunca se modifica al detectar el problema (research.md R10).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from devlog.config import BUSY_TIMEOUT_MS
from devlog.errors import LOCK_ERROR_MESSAGE, STORE_ERROR_MESSAGE, StoreError, StoreLockedError

SQLITE_MAGIC = b"SQLite format 3\x00"

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS notes (
        id         INTEGER PRIMARY KEY,
        title      TEXT    NOT NULL,
        content    TEXT    NOT NULL DEFAULT '',
        created_at TEXT    NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tags (
        id         INTEGER PRIMARY KEY,
        name       TEXT    NOT NULL UNIQUE,
        created_at TEXT    NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS note_tags (
        note_id INTEGER NOT NULL REFERENCES notes(id),
        tag_id  INTEGER NOT NULL REFERENCES tags(id),
        PRIMARY KEY (note_id, tag_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_note_tags_tag ON note_tags(tag_id, note_id)",
)


def _looks_like_sqlite(path: Path) -> bool:
    """Indica si el archivo empieza con la cabecera de un archivo SQLite."""
    try:
        with path.open("rb") as handle:
            return handle.read(len(SQLITE_MAGIC)) == SQLITE_MAGIC
    except OSError:
        return False


def ensure_store_is_readable(path: Path) -> None:
    """Comprueba, sin escribir, que un almacen existente es una base de datos valida.

    Un archivo cuyo contenido no es una base SQLite se rechaza con ``StoreError`` y se
    deja intacto: la herramienta nunca borra ni reconstruye los datos del usuario.
    """
    if not path.exists() or path.stat().st_size == 0:
        return

    probe: sqlite3.Connection | None = None
    try:
        uri = f"{path.resolve().as_uri()}?mode=ro"
        probe = sqlite3.connect(uri, uri=True)
        probe.execute("SELECT count(*) FROM sqlite_master").fetchone()
    except sqlite3.DatabaseError as exc:
        if not _looks_like_sqlite(path):
            raise StoreError(STORE_ERROR_MESSAGE) from exc
        # Tiene cabecera SQLite: el problema es mas profundo y se detectara al abrir.
    finally:
        if probe is not None:
            probe.close()


def _prepare_parent(path: Path) -> None:
    """Crea el directorio del almacen si falta, con permisos solo para el propietario."""
    parent = path.parent
    if parent.exists():
        return
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)


def _connect(path: Path) -> sqlite3.Connection:
    """Abre la conexion con los pragmas del proyecto."""
    try:
        connection = sqlite3.connect(str(path), timeout=BUSY_TIMEOUT_MS / 1000)
    except sqlite3.Error as exc:
        raise StoreError(STORE_ERROR_MESSAGE) from exc
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    except sqlite3.OperationalError as exc:
        connection.close()
        message = str(exc).lower()
        if "locked" in message or "busy" in message:
            raise StoreLockedError(LOCK_ERROR_MESSAGE) from exc
        raise StoreError(STORE_ERROR_MESSAGE) from exc
    except sqlite3.DatabaseError as exc:
        connection.close()
        raise StoreError(STORE_ERROR_MESSAGE) from exc
    return connection


def ensure_schema(connection: sqlite3.Connection) -> None:
    """Crea el esquema de forma aditiva. Nunca borra ni reescribe nada."""
    try:
        with connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
    except sqlite3.OperationalError as exc:
        message = str(exc).lower()
        if "locked" in message or "busy" in message:
            raise StoreLockedError(LOCK_ERROR_MESSAGE) from exc
        raise StoreError(STORE_ERROR_MESSAGE) from exc
    except sqlite3.DatabaseError as exc:
        raise StoreError(STORE_ERROR_MESSAGE) from exc


@contextmanager
def open_store(path: Path) -> Iterator[sqlite3.Connection]:
    """Abre el almacen, garantiza el esquema y cierra la conexion al terminar."""
    ensure_store_is_readable(path)
    _prepare_parent(path)
    connection = _connect(path)
    try:
        ensure_schema(connection)
        yield connection
    finally:
        connection.close()

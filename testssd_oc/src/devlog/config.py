"""Configuracion central de DevLog CLI.

Resuelve la ubicacion del almacen SQLite, los codigos de salida y los valores por
defecto de la exportacion. La ruta del almacen puede sobrescribirse con la variable de
entorno ``DEVLOG_DB_PATH``, que es el mecanismo que usan las pruebas para no tocar
nunca la base de datos real del desarrollador.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "devlog"
APP_VERSION = "0.1.0"

# Codigos de salida (FR-021).
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_NO_RESULTS = 3

# Almacen local (FR-003).
STORE_DIR_NAME = ".devlog"
STORE_FILE_NAME = "notes.db"
DB_PATH_ENV_VAR = "DEVLOG_DB_PATH"

# Exportacion (FR-014).
DEFAULT_EXPORT_FILENAME = "devlog-notes.md"

# Bloqueo de la base de datos (research.md R9).
BUSY_TIMEOUT_MS = 5000


def default_store_path() -> Path:
    """Devuelve la ruta por defecto del almacen: ``~/.devlog/notes.db``."""
    return Path.home() / STORE_DIR_NAME / STORE_FILE_NAME


def resolve_store_path() -> Path:
    """Devuelve la ruta del almacen, honrando ``DEVLOG_DB_PATH`` si esta definida."""
    override = os.environ.get(DB_PATH_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return default_store_path()


def resolve_export_path(output: str | os.PathLike[str] | None) -> Path:
    """Devuelve la ruta del archivo de exportacion.

    Sin ``output`` se usa ``devlog-notes.md`` en el directorio actual.
    """
    if output is None:
        return Path(DEFAULT_EXPORT_FILENAME)
    return Path(output).expanduser()

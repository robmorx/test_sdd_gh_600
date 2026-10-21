"""Errores de dominio de DevLog.

Cada error lleva su propio mensaje en espanol, apto para mostrarse al usuario sin
trazas tecnicas (FR-020), y el codigo de salida con el que debe terminar el proceso
(FR-021).
"""

from __future__ import annotations

from devlog.config import EXIT_ERROR, EXIT_NO_RESULTS, EXIT_USAGE

STORE_ERROR_MESSAGE = (
    "No se pudo abrir la base de datos: el archivo puede estar dañado. "
    "Restaura una copia o mueve el archivo manualmente; no se ha modificado nada."
)

LOCK_ERROR_MESSAGE = (
    "La base de datos está siendo usada por otra operación. "
    "Inténtalo de nuevo en unos segundos."
)


class DevLogError(Exception):
    """Error de dominio con mensaje para el usuario y codigo de salida."""

    exit_code = EXIT_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class StoreError(DevLogError):
    """El almacen no se puede abrir o esta dañado."""


class StoreLockedError(DevLogError):
    """Otra operacion esta usando el almacen en este momento."""


class ExportPathError(DevLogError):
    """La ruta de destino de la exportacion no es utilizable."""


class ValidationError(DevLogError):
    """La entrada del usuario no cumple las reglas del dominio."""

    exit_code = EXIT_USAGE


class NoResultsError(DevLogError):
    """La operacion se completo correctamente pero no encontro resultados."""

    exit_code = EXIT_NO_RESULTS

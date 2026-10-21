"""Fixtures compartidas.

Ninguna prueba toca el almacen real del desarrollador: todas usan un archivo SQLite
temporal a traves de la variable ``DEVLOG_DB_PATH`` (Constitution Principle I, Safety).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence

import pytest
from typer.testing import CliRunner

from devlog import config, db, repository
from devlog.models import Note

SeedSpec = Sequence[tuple[str, Sequence[str], str | None]]


@pytest.fixture
def cli_output() -> Callable[[object], str]:
    """Devuelve una funcion que reune la salida completa de una invocacion."""

    def _output(result) -> str:
        chunks: list[str] = [result.output or ""]
        try:
            if result.stderr:
                chunks.append(result.stderr)
        except ValueError:  # pragma: no cover -click antiguo con stderr combinado
            pass
        return "\n".join(chunk for chunk in chunks if chunk)

    return _output


@pytest.fixture
def store_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Apunta el almacen a un archivo temporal y devuelve su ruta."""
    path = tmp_path / "store" / "notes.db"
    monkeypatch.setenv(config.DB_PATH_ENV_VAR, str(path))
    return path


@pytest.fixture
def runner() -> CliRunner:
    """Ejecutor de comandos para probar la CLI de extremo a extremo."""
    return CliRunner()


@pytest.fixture
def seed_notes(store_path: Path) -> Callable[..., list[Note]]:
    """Devuelve una funcion que crea notas directamente en el almacen."""

    def _seed(
        specs: Iterable[tuple] | None = None,
        count: int = 0,
        tags: Sequence[str] = (),
        title_prefix: str = "Nota",
        content: str = "contenido",
    ) -> list[Note]:
        rows: list[Note] = []
        if specs is None:
            specs = [(f"{title_prefix} {index + 1}", list(tags), None) for index in range(count)]
        with db.open_store(store_path) as connection:
            for spec in specs:
                title, note_tags, created_at = spec[0], spec[1], spec[2]
                body = spec[3] if len(spec) > 3 else content
                rows.append(
                    repository.insert_note(
                        connection,
                        title,
                        body,
                        list(note_tags),
                        created_at=created_at,
                    )
                )
        return rows

    return _seed


@pytest.fixture
def iso(minutes_ago: int = 0) -> Callable[[int], str]:
    """Devuelve una funcion que crea marcas de tiempo UTC desplazadas en minutos."""

    def _iso(offset_minutes: int) -> str:
        moment = datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)
        return moment.strftime("%Y-%m-%dT%H:%M:%SZ")

    return _iso

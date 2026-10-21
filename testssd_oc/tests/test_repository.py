"""Pruebas de la capa de almacenamiento."""

from __future__ import annotations

from pathlib import Path

import pytest

from devlog import db, repository
from devlog.errors import StoreError


def test_insert_note_persists_the_note_and_its_tags(store_path: Path) -> None:
    with db.open_store(store_path) as connection:
        note = repository.insert_note(connection, "CORS error in staging", "detalle", ["bug", "api"])

    assert note.id > 0
    with db.open_store(store_path) as connection:
        stored = repository.list_notes(connection)

    assert len(stored) == 1
    assert stored[0].title == "CORS error in staging"
    assert stored[0].content == "detalle"
    assert stored[0].tags == ("api", "bug")


def test_note_can_be_stored_without_tags(store_path: Path) -> None:
    with db.open_store(store_path) as connection:
        repository.insert_note(connection, "Sin etiquetas", "", [])
        stored = repository.list_notes(connection)
        tags = repository.get_tags_for_note(connection, stored[0].id)

    assert stored[0].tags == ()
    assert tags == []


def test_same_tag_is_reused_across_notes(store_path: Path) -> None:
    with db.open_store(store_path) as connection:
        repository.insert_note(connection, "Una", "", ["bug"])
        repository.insert_note(connection, "Dos", "", ["bug"])
        tags = connection.execute("SELECT COUNT(*) AS total FROM tags").fetchone()

    assert tags["total"] == 1


def test_duplicate_tag_inside_one_note_is_stored_once(store_path: Path) -> None:
    with db.open_store(store_path) as connection:
        repository.insert_note(connection, "Repetida", "", ["bug", "bug", "BUG"])
        links = connection.execute("SELECT COUNT(*) AS total FROM note_tags").fetchone()

    assert links["total"] == 1


def test_list_notes_is_ordered_newest_first_with_id_tiebreak(store_path: Path) -> None:
    with db.open_store(store_path) as connection:
        repository.insert_note(connection, "Antigua", "", [], created_at="2026-01-01T10:00:00Z")
        repository.insert_note(connection, "Misma hora A", "", [], created_at="2026-01-02T10:00:00Z")
        repository.insert_note(connection, "Misma hora B", "", [], created_at="2026-01-02T10:00:00Z")
        stored = repository.list_notes(connection)

    assert [note.title for note in stored] == ["Misma hora B", "Misma hora A", "Antigua"]


def test_search_requires_every_requested_tag(store_path: Path) -> None:
    with db.open_store(store_path) as connection:
        repository.insert_note(connection, "Bug y api", "", ["bug", "api"])
        repository.insert_note(connection, "Solo bug", "", ["bug"])
        repository.insert_note(connection, "Sin etiquetas", "", [])

        both = repository.search_notes_by_tags(connection, ["bug", "api"])
        one = repository.search_notes_by_tags(connection, ["bug"])
        none = repository.search_notes_by_tags(connection, ["desconocida"])

    assert [note.title for note in both] == ["Bug y api"]
    assert [note.title for note in one] == ["Solo bug", "Bug y api"]
    assert none == []


def test_search_returns_all_tags_of_the_matching_note(store_path: Path) -> None:
    with db.open_store(store_path) as connection:
        repository.insert_note(connection, "Con extras", "", ["bug", "api", "idea"])
        results = repository.search_notes_by_tags(connection, ["bug"])

    assert results[0].tags == ("api", "bug", "idea")


def test_count_notes_returns_the_total(store_path: Path) -> None:
    with db.open_store(store_path) as connection:
        repository.insert_note(connection, "Una", "", [])
        repository.insert_note(connection, "Dos", "", [])
        assert repository.count_notes(connection) == 2


def test_corrupted_store_raises_store_error_and_leaves_the_file_untouched(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"esto no es una base de datos")
    before = corrupt.read_bytes()

    with pytest.raises(StoreError):
        with db.open_store(corrupt):
            pass

    assert corrupt.read_bytes() == before

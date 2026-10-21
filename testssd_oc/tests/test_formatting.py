"""Pruebas de las unidades de formato y normalizacion."""

from __future__ import annotations

from datetime import datetime, timezone

from devlog.formatting import (
    format_local_datetime,
    format_note_line,
    format_tag_list,
    normalize_tag,
    split_tags,
)
from devlog.models import Note


def test_normalize_tag_trims_and_lowercases() -> None:
    assert normalize_tag("  Bug ") == "bug"
    assert normalize_tag("API") == "api"


def test_split_tags_splits_commas_trims_lowercases_and_deduplicates() -> None:
    assert split_tags(["Bug", " api , idea", "bug", "", "   "]) == ["bug", "api", "idea"]


def test_split_tags_returns_empty_list_for_empty_input() -> None:
    assert split_tags([]) == []
    assert split_tags(None) == []


def test_format_local_datetime_renders_local_time_with_minutes() -> None:
    expected = datetime(2026, 10, 21, 9, 30, tzinfo=timezone.utc).astimezone().strftime(
        "%Y-%m-%d %H:%M"
    )
    assert format_local_datetime("2026-10-21T09:30:00Z") == expected


def test_format_tag_list_without_tags_uses_placeholder() -> None:
    assert format_tag_list(()) == "(sin etiquetas)"
    assert format_tag_list(("bug", "api")) == "bug, api"


def test_format_note_line_keeps_the_title_at_the_end() -> None:
    note = Note(id=12, title="CORS error in staging", content="", created_at="2026-10-21T09:30:00Z")
    line = format_note_line(note)
    assert line.startswith("#12  ")
    assert line.endswith("CORS error in staging")
    assert "(sin etiquetas)" in line

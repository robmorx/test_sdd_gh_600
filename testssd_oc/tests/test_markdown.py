"""Pruebas del generador de Markdown (`contracts/markdown-export.md`)."""

from __future__ import annotations

from devlog.markdown import escape_title, fence_body, render_document
from devlog.models import Note

NOTE = Note(
    id=12,
    title="CORS error in staging",
    content="El servidor rechaza el preflight OPTIONS.\nRevisar el header.",
    created_at="2026-10-21T09:30:00Z",
    tags=("api", "bug"),
)


def test_document_has_the_expected_structure() -> None:
    document = render_document([NOTE], "2026-10-21T09:32:00Z")

    assert document.startswith("# Notas de DevLog\n")
    assert "## #12 · CORS error in staging" in document
    assert "- **Creado**: " in document
    assert "- **Etiquetas**: `api`, `bug`" in document
    assert document.rstrip().endswith("Revisar el header.")


def test_note_without_tags_uses_the_placeholder() -> None:
    note = Note(id=11, title="Useful psql snippet", content="", created_at="2026-10-20T18:05:00Z")
    document = render_document([note], "2026-10-21T09:32:00Z")

    assert "- **Etiquetas**: (sin etiquetas)" in document


def test_body_is_written_verbatim() -> None:
    body = "- uno\n- dos\n\n  sangrado y \"comillas\""
    note = Note(id=1, title="Lista", content=body, created_at="2026-10-21T09:30:00Z")

    document = render_document([note], "2026-10-21T09:32:00Z")

    assert body in document


def test_title_is_escaped_so_it_cannot_break_the_structure() -> None:
    note = Note(id=1, title="*.Title* with # and [brackets]", content="", created_at="2026-10-21T09:30:00Z")

    document = render_document([note], "2026-10-21T09:32:00Z")

    assert r"\*.Title\* with \# and \[brackets\]" in document


def test_escape_title_escapes_markdown_control_characters() -> None:
    assert escape_title("a*b_c`d") == r"a\*b\_c\`d"
    assert escape_title("- al principio") == r"\- al principio"
    assert escape_title("normal") == "normal"


def test_body_with_backtick_fence_gets_a_longer_fence() -> None:
    body = "```bash\necho hola\n```"

    fenced = fence_body(body)

    assert fenced.startswith("````")
    assert fenced.endswith("````")
    assert body in fenced


def test_body_without_backticks_is_not_fenced() -> None:
    assert fence_body("texto normal") == "texto normal"


def test_empty_document_is_valid() -> None:
    document = render_document([], "2026-10-21T09:32:00Z")

    assert document.startswith("# Notas de DevLog\n")
    assert "0 notas" in document
    assert "##" not in document

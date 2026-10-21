# Phase 1 Data Model: DevLog CLI

**Feature**: `001-devlog-cli` | **Date**: 2026-10-21
**Canonical path**: `specs/001-devlog-cli/data-model.md`
**Sources**: `spec.md` (Key Entities, FR-001..FR-021, Edge Cases), `research.md` (R1, R7, R11, R12)

Storage engine: a single SQLite file (R1). The schema below is the *logical* model; the
physical representation is documented alongside each entity so that the storage layer can
be implemented without re-deriving decisions.

## Entity Relationship Overview

```text
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│     Note     │        │     NoteTag      │        │     Tag      │
├──────────────┤        ├──────────────────┤        ├──────────────┤
│ id      (PK) │───1:N──│ note_id  (PK, FK)│───N:1──│ id      (PK) │
│ title       │        │ tag_id   (PK, FK) │        │ name (UNIQUE)│
│ content     │        └──────────────────┘        │ created_at   │
│ created_at  │                                    └──────────────┘
└──────────────┘
   Note 1 ── 0..N NoteTag  N ── 1 Tag
```

A note has **zero or more** tags; a tag may be shared by many notes; the same tag can
never appear twice within one note (FR-017, enforced structurally — R12).

## Note

The central record of the product (spec Key Entities). Created, listed, searched, and
exported.

| Field | Type | Required | Rules |
|---|---|---|---|
| `id` | integer | yes | Assigned by the store, unique, immutable, never reused. Rendered to the user as `#<id>` (R11). |
| `title` | text | yes | Must not be empty and must not consist solely of spaces (FR-016). Stored with surrounding whitespace trimmed. No maximum length is imposed in v1. |
| `content` | text | no | Optional. Defaults to an empty string. Preserved byte-for-byte: line breaks, lists, quotes, and Markdown characters are never altered (FR-018). |
| `created_at` | text | yes | UTC ISO-8601 timestamp (`YYYY-MM-DDTHH:MM:SSZ`), assigned by the tool at creation time and never modified afterwards (FR-002). Displayed to the user in local time as `YYYY-MM-DD HH:MM` (R7). |

**Validation rules**

| Rule | Source | Failure behaviour |
|---|---|---|
| Title is not empty after trimming | FR-016 | Rejected, nothing is saved, exit code 2, message in Spanish. |
| Title is not whitespace-only | FR-016 | Same as above. |
| Content is any text, including empty | FR-018 | Accepted. |
| Tags are trimmed and lowercased | FR-017 | Applied before storage; the user sees the normalised value in the confirmation. |

**Lifecycle / state transitions**

```text
            ┌──────────────┐
   create ─▶│  persisted   │◀── list / search / export (read-only)
            └──────────────┘
                 │
                 │ (no edit, no delete in v1 — R3)
                 ▼
             terminal state for v1
```

A note has exactly one persisted state in v1. `Export Result` is derived from notes and
never written back to the store, so exporting cannot alter or duplicate notes (spec Key
Entities: "it does not become part of the notes again").

## Tag

The user classification mechanism: a short, free-form text label with no hierarchy, no
colour, and no predefined vocabulary.

| Field | Type | Required | Rules |
|---|---|---|---|
| `id` | integer | yes | Assigned by the store, unique, internal. |
| `name` | text | yes | Trimmed and lowercased before storage (FR-017). Unique across the store; because names are normalised, the uniqueness is effectively case-insensitive (R12). A note may have no tags at all. |
| `created_at` | text | yes | UTC ISO-8601 timestamp of first use of the tag. |

**Validation rules**

| Rule | Source | Failure behaviour |
|---|---|---|
| Empty or whitespace-only tags are discarded, not stored | FR-017 | The tag is ignored; the note is still created with its remaining tags. |
| The same tag repeated within one note is stored once | FR-017 | Enforced by the `note_tags` primary key — the duplicate insert is simply never performed. |
| The same tag with different capitalisation within one note is one tag | FR-017 | Normalisation happens before the write. |

## NoteTag (join entity)

| Field | Type | Required | Rules |
|---|---|---|---|
| `note_id` | integer | yes | Foreign key to `Note.id`. |
| `tag_id` | integer | yes | Foreign key to `Tag.id`. |

The pair `(note_id, tag_id)` is the primary key, which is what makes duplicate tags
within a note structurally impossible (R12). Foreign keys are enforced at runtime
(`PRAGMA foreign_keys=ON`).

## Export Result

A derived artefact, not a stored record.

| Field | Type | Rules |
|---|---|---|
| `path` | text | Absolute or relative filesystem path of the generated Markdown file. |
| `note_count` | integer | Number of notes included in the export (may be 0 — an empty but valid file is produced). |
| `generated_at` | text | UTC ISO-8601 timestamp of the export, shown inside the document header. |

**Rules**

- The export contains every note in the store, ordered newest first, with title, creation
  date, tags, and content (FR-013).
- Exporting never modifies the store (spec Key Entities).
- When the store holds no notes, an empty but valid Markdown file is produced and the
  user is told there was nothing to export (spec Edge Cases).

## Physical Schema (reference)

The logical model maps to three tables. The statements below are the *only* schema
operations the tool is allowed to perform; anything else would violate Constitution
Principle II.

```sql
CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY,
    title      TEXT    NOT NULL,
    content    TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id         INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL UNIQUE,
    created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER NOT NULL REFERENCES notes(id),
    tag_id  INTEGER NOT NULL REFERENCES tags(id),
    PRIMARY KEY (note_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_note_tags_tag ON note_tags(tag_id, note_id);
```

Supporting pragmas applied on every connection: `journal_mode=WAL`,
`foreign_keys=ON`, `busy_timeout=5000` (R9).

**Migration rule**: future schema changes use additive `ALTER TABLE ... ADD COLUMN`
statements only. `DROP`, `TRUNCATE`, `DELETE`, table rewrites, and store resets are
forbidden without explicit, per-operation user approval recorded at the moment of
execution (Constitution Principle II, FR-019).

## Query Contracts

| Query | Semantics | Ordering |
|---|---|---|
| `list_notes` | All notes, unfiltered | `created_at DESC, id DESC` (newest first, FR-007) |
| `search_by_tags(tags)` | Notes carrying **every** requested tag, matched **exactly** against the normalised tag name (R2) | `created_at DESC, id DESC` |
| `count_notes` | Total note count | — |
| `insert_note` | Inserts the note and its tag links in one transaction; reuses an existing tag row when the normalised name already exists | — |

A note with no tags is returned by `list_notes` but never by `search_by_tags` (search
requires at least one tag to match).

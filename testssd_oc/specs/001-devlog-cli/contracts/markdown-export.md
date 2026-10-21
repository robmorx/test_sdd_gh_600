# Contract: DevLog Markdown Export Format

**Feature**: `001-devlog-cli` | **Date**: 2026-10-21
**Canonical path**: `specs/001-devlog-cli/contracts/markdown-export.md`
**Sources**: `spec.md` (FR-013, FR-015, FR-018, SC-006, Edge Cases), `research.md` (R8)

The file produced by `devlog export` is a human-readable Markdown document that contains
every note in the store. This contract fixes the layout so the export can be asserted
byte-for-byte in tests.

## 1. Document structure

```text
# Notas de DevLog

<generated_at> · <note_count> nota(s)

---

## #<id> · <title>

**<etiquetas line>**
**<created_at> line**

<body>

---
```

Rules:

1. The document starts with a single level-1 heading, `Notas de DevLog`.
2. A second line records the generation timestamp (local time, `YYYY-MM-DD HH:MM`) and
   the number of exported notes.
3. A horizontal rule separates the header from the notes.
4. Each note is one level-2 section: `## #<id> · <title>` — the id is prefixed with `#`
   and the two parts are separated by ` · `.
5. Each note is followed by two metadata lines and then the body.
6. A horizontal rule separates consecutive notes.
7. The file ends with a trailing newline.

## 2. Metadata lines

```text
- **Creado**: 2026-10-21 09:30
- **Etiquetas**: `bug`, `api`
```

- `Creado` is the note's creation date in local time, `YYYY-MM-DD HH:MM` (R7).
- `Etiquetas` lists the note's normalised tags, each wrapped in backticks, comma-separated
  in ascending alphabetical order. A note with no tags shows `- **Etiquetas**: (sin etiquetas)`.
- The date line always comes first, then the tag line.

## 3. Body rendering — verbatim by default (R8, FR-018, SC-006)

The body is written **exactly as stored**: no escaping, no re-flowing, no trimming of
inner whitespace, no normalisation of line endings inside the body beyond reading the
file as UTF-8 text.

- Line breaks are preserved, so lists and code blocks inside a note stay readable.
- Quotes, backslashes, asterisks, and other special characters are preserved.
- This guarantees SC-006: extracting the body from the exported document returns the
  original text byte-for-byte.

### 3.1 The one exception — pathological fenced blocks

If the body contains a line made of **three or more consecutive backticks**, the body is
wrapped in a fence that is longer than that run (the fence length is
`max(3, longest_backtick_run + 1)`), so the body cannot terminate the block early:

```text
````
```bash
echo "hola"
```
````
```

The body inside the fence is still byte-for-byte identical; only the fence is added, and
only when strictly necessary.

### 3.2 Title escaping (the only other transformation)

The note title is escaped so that it can never break the document structure. The
characters escaped with a backslash are:

```text
\  `  *  _  { } [ ] ( ) # + - . ! | < >
```

Escaping is applied only to the title, because the title is inserted into a heading
where it would otherwise be interpreted as Markdown syntax. The body is never escaped
(section 3).

## 4. Worked example

For a store containing two notes — `#12` titled `CORS error in staging` with tags `api`
and `bug`, and `#11` titled `Useful psql snippet` with no tags — the export is:

```markdown
# Notas de DevLog

2026-10-21 09:32 · 2 notas

---

## #12 · CORS error in staging

- **Creado**: 2026-10-21 09:30
- **Etiquetas**: `api`, `bug`

El servidor rechaza el preflight OPTIONS.
Revisar el header Access-Control-Allow-Origin.

---

## #11 · Useful psql snippet

- **Creado**: 2026-10-20 18:05
- **Etiquetas**: (sin etiquetas)

```sql
SELECT * FROM notas WHERE id = 1;
```
```

Note that the notes are ordered newest first and that the inner code fence in the second
body is closed correctly because the body contains no run of three backticks on its own
line.

## 5. Empty export

When the store holds no notes, the tool still writes a valid, empty document:

```markdown
# Notas de DevLog

2026-10-21 09:32 · 0 notas

---
```

The command reports `No había notas para exportar.` and exits with code `0`
(spec Edge Cases).

## 6. Overwrite policy

The destination file follows the rules in `contracts/cli.md` §5: confirm before
replacing, or replace with an explicit `--force`, and never replace silently in a
non-interactive session. The exported document always fully replaces the previous
content of the destination file — no merging, no appending, no partial writes. A failed
write leaves no partial file behind.

## 7. Verification hooks

| Property | How it is checked |
|---|---|
| All notes are present (SC-006) | Count the `## #` headings; compare with the store's note count. |
| Title, date, tags, and content are present (FR-013) | Assert the presence of each expected field per section. |
| Content is not corrupted (SC-006) | Extract each body and compare it byte-for-byte with the stored body. |
| Readability of lists and line breaks (US4 scenario 3) | Assert the body section contains the original line structure. |

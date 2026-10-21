# Contract: DevLog CLI Command Interface

**Feature**: `001-devlog-cli` | **Date**: 2026-10-21
**Canonical path**: `specs/001-devlog-cli/contracts/cli.md`
**Sources**: `spec.md` (US1–US4, FR-001..FR-025, Edge Cases), `research.md` (R4, R5, R6, R13)

This is the public contract of the tool. Every command, flag, message shape, and exit
code listed here is a testable commitment; anything not listed here is an implementation
detail and may change without notice.

## 1. Global Contract

| Aspect | Contract |
|---|---|
| Invocation | `devlog <command> [options]`, or `python -m devlog <command> [options]` |
| Interface language | Spanish — all help text, confirmations, warnings, and errors (spec Assumptions) |
| Store location | `~/.devlog/notes.db`, overridable with the `DEVLOG_DB_PATH` environment variable (R1) |
| First run | The store and its schema are created automatically, without prompting, without touching any pre-existing file (spec Edge Cases) |
| Network | None. The tool never opens a network connection (FR-023) |
| Authentication | None. No accounts, passwords, sessions, or tokens (FR-022) |
| Output | Plain text on stdout; diagnostics on stderr. No colour codes, no progress bars, no tables |

### Exit codes (R5, FR-021)

| Code | Meaning | When it is produced |
|---|---|---|
| `0` | Success | The operation completed. An empty listing and an export of zero notes are successes. |
| `1` | Operational error | Store cannot be opened or is corrupted; destination path is not writable; the database is locked by another operation; the export file could not be written. |
| `2` | Usage or validation error | Unknown command or option; missing required argument; the note title is empty or whitespace-only. |
| `3` | No results | A tag search completed successfully and matched no note. |

### Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `DEVLOG_DB_PATH` | Absolute or relative path of the SQLite store. Used by the test suite to isolate from the developer's real notes (R1, Constitution Principle I / Safety). | `~/.devlog/notes.db` |

---

## 2. `devlog add` — create a note (US1, P1)

Creates one note with a mandatory title, optional content, and zero or more tags.

**Usage**

```text
devlog add [OPTIONS] TITLE

Arguments:
  TITLE  Title of the note. Required; rejected when empty or whitespace-only.

Options:
  -t, --tag TEXT           Tag to attach. Repeatable. A comma-separated value is split
                           into several tags. Duplicates and case differences collapse
                           into one normalised tag.
  -c, --content TEXT       Body of the note, given inline.
  --content-file PATH      Read the body from a file. Use "-" to read it from standard
                           input (the way to enter multi-line content).
  --title TEXT             Alternative to the positional TITLE argument.
  --help                   Show the help text.
```

**Input rules**

- Exactly one of the positional `TITLE` or `--title` must be supplied.
- If neither `--content` nor `--content-file` is given and standard input is not a
  terminal, standard input is read as the body.
- Tags are trimmed and lowercased; empty tags are discarded; a tag repeated within the
  command is stored once (FR-017).
- The body is stored verbatim — line breaks and special characters are preserved exactly
  (FR-018).

**Output on success (stdout)**

```text
Nota #12 guardada (2026-10-21 09:30).
Etiquetas: bug, api
```

- The creation date is shown in local time as `YYYY-MM-DD HH:MM`.
- The tag line is omitted when the note has no tags.

**Errors**

| Condition | Message | Exit code |
|---|---|---|
| Title empty or whitespace-only | `El título no puede estar vacío.` | `2` |
| Title missing entirely | `Missing argument "TITLE".` (Typer usage error) | `2` |
| Store cannot be opened or is corrupted | `No se pudo abrir la base de datos: el archivo puede estar dañado. Restaura una copia o mueve el archivo manualmente; no se ha modificado nada.` | `1` |
| Database locked by another operation | `La base de datos está siendo usada por otra operación. Inténtalo de nuevo en unos segundos.` | `1` |

**Acceptance coverage**: US1 scenarios 1–3; FR-001, FR-002, FR-016, FR-017, FR-018,
FR-020, FR-021.

---

## 3. `devlog list` — list notes (US2, P2)

Lists every saved note, newest first.

**Usage**

```text
devlog list [OPTIONS]

Options:
  --help  Show the help text.
```

**Output format (R13)** — one note per line, in this order:

```text
#<id>  <YYYY-MM-DD HH:MM>  [<tag>, <tag>]  <title>
```

- The id is prefixed with `#`.
- The date is the local-time creation date.
- The tag list is comma-separated inside brackets; a note with no tags shows
  `(sin etiquetas)`.
- The title is last so that long titles are never truncated.
- Ordering is newest first, with the note id as tiebreaker for notes created in the same
  second (FR-007, R7).

**Example**

```text
#12  2026-10-21 09:30  [bug, api]  CORS error in staging
#11  2026-10-20 18:05  (sin etiquetas)  Useful psql snippet
```

**Special cases**

| Situation | Behaviour | Exit code |
|---|---|---|
| No notes saved | `No hay notas guardadas todavía.` on stdout, no error, no traceback (US2 scenario 2) | `0` |
| A note without tags | The note still appears, showing `(sin etiquetas)` (US2 scenario 3) | `0` |
| 500 notes | All 500 lines are printed, none omitted or duplicated (SC-003), in under 3 seconds (SC-004) | `0` |

**Acceptance coverage**: US2 scenarios 1–3; FR-005..FR-008.

---

## 4. `devlog search` — search notes by tag (US3, P3)

Returns the notes that carry the requested tags.

**Usage**

```text
devlog search [OPTIONS] TAG [TAG]...

Arguments:
  TAG  Tag to search for. At least one is required. Repeatable or comma-separated.

Options:
  --help  Show the help text.
```

**Matching rules (R2, FR-010)**

| Rule | Behaviour |
|---|---|
| Exact match | The tag must equal the requested tag after normalisation (trim + lowercase). `api` does **not** match `apiary`. |
| Multiple tags | AND — a note is returned only if it carries **every** requested tag. |
| Normalisation | `Bug`, ` bug `, and `bug` are the same tag. |
| No tags | `devlog search` with no tag is a usage error. |
| Untagged notes | A note without tags is never returned by a search. |

**Output format** — identical to `devlog list` (R13), restricted to matching notes, same
ordering.

**Special cases**

| Situation | Behaviour | Exit code |
|---|---|---|
| No matches | `No se encontraron notas con esas etiquetas.` on stdout, clearly distinguished from an error (US3 scenario 2, FR-011) | `3` |
| Matches found | One line per matching note with id, date, and tags (US3 scenario 3) | `0` |
| Tag that does not exist anywhere | Same as "no matches" | `3` |

**Acceptance coverage**: US3 scenarios 1–3; FR-009, FR-010, FR-011.

---

## 5. `devlog export` — export notes to Markdown (US4, P4)

Writes every saved note to a Markdown file.

**Usage**

```text
devlog export [OPTIONS]

Options:
  -o, --output PATH   Destination file. Parent directories must already exist.
                      Default: ./devlog-notes.md
  --force             Replace the destination file without asking for confirmation.
                      Counts as explicit confirmation given at that moment.
  --help              Show the help text.
```

**Behaviour**

1. Notes are exported newest first, each with its id, title, creation date, tags, and
   content (FR-013).
2. If the destination does not exist, the file is created.
3. If the destination **does** exist, the tool asks:
   `El archivo ya existe: <ruta>. ¿Quieres sobrescribirlo? [s/N]` and waits for an
   answer. Only an explicit yes proceeds.
4. With `--force`, the file is replaced without asking.
5. In a non-interactive session (standard input is not a terminal) without `--force`, the
   tool refuses: `El archivo ya existe y no se puede pedir confirmación. Usa --force o
   indica otra ruta con --output.` and leaves the existing file untouched.
6. If the store holds no notes, an empty but valid Markdown file is produced and the user
   is told `No había notas para exportar.` (spec Edge Cases).

**Output on success (stdout)**

```text
Notas exportadas a devlog-notes.md (3 notas).
```

**Errors**

| Condition | Message | Exit code |
|---|---|---|
| Parent directory does not exist | `No existe el directorio de destino: <dir>.` | `1` |
| Destination is not writable | `No se pudo escribir el archivo: <ruta>.` | `1` |
| Export refused because confirmation was impossible | Message shown in step 5 above | `1` |
| Store corrupted | Same message as in `devlog add` | `1` |

**Acceptance coverage**: US4 scenarios 1–3; FR-012..FR-015, FR-018.

---

## 6. Error and Message Contract (FR-020)

| Rule | Commitment |
|---|---|
| No stack traces | A failure never prints a Python traceback or an internal path of the implementation. |
| Cause + action | Every error names what failed and what the user should do next. |
| No partial artefacts | A failed export leaves no partial file behind (spec Edge Cases). |
| Corruption is never repaired automatically | The tool explains and stops; it never deletes, resets, or recreates the store (R10, Constitution Principle II). |
| Destructive confirmation | Any action that would replace an existing file requires an explicit, immediate confirmation (FR-015, FR-019). |

---

## 7. Out of Contract (explicitly not part of v1)

Editing notes, deleting notes, free-text search over title or content, note categories,
file or image attachments, cloud synchronisation, export formats other than Markdown,
JSON or other machine-readable output, authentication, multi-user stores, a graphical
interface, and editor integration (spec Assumptions, R3, R13).

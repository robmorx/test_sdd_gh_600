# Quickstart: Validating DevLog CLI

**Feature**: `001-devlog-cli` | **Date**: 2026-10-21
**Canonical path**: `specs/001-devlog-cli/quickstart.md`

A runnable guide that proves the feature works end to end. Every command below is
expected to be executed from the repository root. For the command, flag, exit-code, and
message details, see `contracts/cli.md`; for the export layout, see
`contracts/markdown-export.md`; for the entity rules, see `data-model.md`.

> **Safety**: every scenario below runs against a throwaway store through
> `DEVLOG_DB_PATH`. Never point the validation runs at `~/.devlog/notes.db` — the real
> notes must not be touched by a validation run (Constitution Principle I, Safety).

## 1. Prerequisites

| Requirement | Check | Notes |
|---|---|---|
| Python 3.11+ | `python3 --version` | The local machine reports 3.14.7. |
| `uv` (recommended) or `venv` + `ensurepip` | `uv --version` | The system interpreter ships without a `pip` module, so `uv` is the documented bootstrap path (R15). |
| No network needed at runtime | — | The tool never opens a network connection (FR-023). |

## 2. Bootstrap the environment

```bash
cd /home/rober/Documentos/ssd-test/testssd_oc

uv venv                                   # creates ./.venv
source .venv/bin/activate
uv pip install -e ".[dev]"                # installs the package in editable mode + pytest
```

Expected outcome: the environment is created, `devlog` becomes available on the `PATH`,
and `pytest` is installed. The install pulls exactly the justified dependency set:
`typer` (with `click`, `typing-extensions`, `shellingham`, `rich`) at runtime and
`pytest` (with `pluggy`, `iniconfig`, `packaging`) for development (R14).

Fallback without `uv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m ensurepip --upgrade
python3 -m pip install -e ".[dev]"
```

## 3. Confirm the CLI is wired up

```bash
devlog --help
```

Expected outcome: the Spanish help text lists the four commands — `add`, `list`,
`search`, `export` — and the global `--help` option.

```bash
python -m devlog --help
```

Expected outcome: the same output; the module entry point works (R15).

## 4. Scenario A — create notes (US1)

```bash
export DEVLOG_DB_PATH="$(mktemp -d)/devlog-notes.db"

devlog add "CORS error in staging" \
  --content "El servidor rechaza el preflight OPTIONS." \
  --tag bug --tag api

devlog add "Useful psql snippet" --content-file ./fixtures/snippet.sql
devlog add "Idea: cachear respuestas" -t idea
```

Expected outcome:

```text
Nota #1 guardada (2026-10-21 09:30).
Etiquetas: bug, api
```

- The first note reports its tags; the third note reports `Etiquetas: idea`.
- The second note reads its body from a file, preserving its line breaks.
- Three notes now exist; no network was used; the store was created automatically.

### Variant — validation failure (FR-016)

```bash
devlog add "   "
```

Expected outcome: `El título no puede estar vacío.`, exit code `2`, and **nothing** is
written to the store.

### Variant — stdin body (R6)

```bash
printf 'linea 1\nlinea 2\n' | devlog add "Nota desde stdin" --content-file -
```

Expected outcome: the note is created with a two-line body; `devlog export` later shows
both lines.

### Variant — tag normalisation (FR-017)

```bash
devlog add "Duplicados" --tag "Bug" --tag " bug " --tag bug
```

Expected outcome: the note carries a single tag, shown as `bug` in the confirmation.

## 5. Scenario B — list notes (US2)

```bash
devlog list
```

Expected outcome: one line per note, newest first, in the form
`#<id>  <YYYY-MM-DD HH:MM>  [<tags>]  <title>`; the untagged note shows
`(sin etiquetas)`; all three notes appear with nothing omitted or duplicated.

### Variant — empty store (US2 scenario 2)

```bash
DEVLOG_DB_PATH="$(mktemp -d)/empty.db" devlog list
```

Expected outcome: `No hay notas guardadas todavía.`, exit code `0`, no error output.

## 6. Scenario C — search by tag (US3)

```bash
devlog search bug
devlog search bug api
devlog search inexistente
```

Expected outcome:

- `search bug` returns only the note tagged `bug`.
- `search bug api` returns only the note carrying **both** tags (AND semantics, R2) —
  if the note from Scenario A does not carry both, the result is empty.
- `search inexistente` prints `No se encontraron notas con esas etiquetas.` and exits
  with code `3` (not an error).

## 7. Scenario D — export to Markdown (US4)

```bash
devlog export
cat devlog-notes.md

devlog export --output ./export/notes.md
```

Expected outcome:

- `devlog-notes.md` is created in the current directory and contains the H1 title, one
  `## #<id> · <title>` section per note, the creation date, the tags, and the body
  verbatim.
- The file content matches the layout in `contracts/markdown-export.md`.
- The command prints `Notas exportadas a devlog-notes.md (3 notas).`

### Variant — overwrite requires confirmation (FR-015)

```bash
devlog export                 # destination already exists → confirmation prompt
devlog export --force         # explicit consent → replaces without asking
```

Expected outcome: the first run asks
`El archivo ya existe: devlog-notes.md. ¿Quieres sobrescribirlo? [s/N]` and only
overwrites when the answer is affirmative; the second run replaces the file
immediately.

### Variant — non-interactive refusal

```bash
devlog export < /dev/null
```

Expected outcome: the tool refuses with
`El archivo ya existe y no se puede pedir confirmación. Usa --force o indica otra ruta con --output.`,
exit code `1`, and the existing file is left untouched.

### Variant — unwritable destination (spec Edge Cases)

```bash
devlog export --output /nonexistent-dir/notes.md
```

Expected outcome: `No existe el directorio de destino: /nonexistent-dir.` exit code `1`,
and no partial file is left anywhere.

## 8. Scenario E — persistence across runs (FR-004)

```bash
devlog list          # same notes still present
```

Expected outcome: the notes from the earlier session are still there, unchanged, after
the process exits and a new process starts.

## 9. Automated test suite (Constitution Principle I, SC-008)

```bash
source .venv/bin/activate
pytest -q
```

Expected outcome: the whole suite passes, with one test module per command covering the
success path, the validation-failure path, and the operational-error path:

| Module | Covers |
|---|---|
| `tests/test_cli_add.py` | US1, FR-001/002/016/017/018 |
| `tests/test_cli_list.py` | US2, FR-005..FR-008, SC-003 completeness |
| `tests/test_cli_search.py` | US3, FR-009..FR-011, exit code `3` |
| `tests/test_cli_export.py` | US4, FR-012..FR-015, overwrite policy |
| `tests/test_repository.py` | Storage layer, uniqueness constraints, WAL/busy behaviour |
| `tests/test_markdown.py` | Escaping rules, byte-for-byte body preservation |
| `tests/test_performance.py` | SC-004 (500 notes < 3 s) and SC-006 (500-note export) |

Each test creates its own temporary store, so the suite never touches
`~/.devlog/notes.db` and needs no network.

## 10. Scenario F — corrupted store is never destroyed (R10, Constitution Principle II)

```bash
TMPDIR_STORE="$(mktemp -d)/corrupt.db"
printf 'not a database' > "$TMPDIR_STORE"
DEVLOG_DB_PATH="$TMPDIR_STORE" devlog list
```

Expected outcome: a clear Spanish message explains that the file may be damaged and
suggests restoring a backup or moving the file aside manually; exit code `1`; and the
file still exists with its original content — the tool never deletes or recreates it.

## 11. Scenario G — concurrent operations (spec Edge Cases, R9)

```bash
( devlog add "Concurrente A" & devlog add "Concurrente B" & wait )
```

Expected outcome: both operations complete (the second one waits for the lock up to
five seconds) and the store contains both notes with no corruption. If the lock cannot
be obtained, the second operation fails with the Spanish lock message and exit code `1`
rather than corrupting the data.

## 12. Cleanup

```bash
rm -f devlog-notes.md
rm -rf "$(dirname "$DEVLOG_DB_PATH")"
```

The real store at `~/.devlog/notes.db` is never touched by these scenarios and must not
be deleted by them.

## Definition of Done for this feature

- [ ] Every command in `contracts/cli.md` behaves as specified, including exit codes.
- [ ] The full test suite passes with no network access (SC-008).
- [x] The three specification clarifications (FR-003, FR-010, FR-012) are folded into
      `spec.md` and the checklist item "No `[NEEDS CLARIFICATION]` markers remain" is
      checked.
- [ ] Listing 500 notes completes in under 3 seconds (SC-004).
- [ ] Exporting 500 notes preserves every note byte-for-byte (SC-006).
- [ ] No destructive operation on the store was executed without recorded, explicit,
      per-operation approval (Constitution Principle II).
- [ ] The dependency set is exactly the justified list in `research.md` R14, pinned in
      `pyproject.toml` and the lockfile (Constitution Principle IV).

---

description: "Task list for DevLog CLI implementation"
---

# Tasks: DevLog CLI

**Input**: Design documents from `/specs/001-devlog-cli/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks ARE included — the specification requires them explicitly (FR-024: "Each tool capability (create, list, search, and export) MUST have automated tests covering both the success path and error paths, and the tests MUST NOT depend on external services or the network"; SC-008).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Tech stack** (from plan.md): Python 3.11+, Typer `>=0.12,<1.0`, standard-library `sqlite3`, pytest `>=8,<9`. Runtime dependency set approved in research.md R14: `typer` (+ `click`, `typing-extensions`, `shellingham`, `rich`); dev: `pytest` (+ `pluggy`, `iniconfig`, `packaging`). No ORM, no migration framework, no HTTP client.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/devlog/` package, `tests/` at repository root, `pyproject.toml` at root
- All user-facing output (help, confirmations, errors) is in **Spanish** (spec Assumptions)
- All source files are UTF-8 and use 4-space indentation, type hints on public functions, and `from __future__ import annotations` where forward references are needed

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create `pyproject.toml` with PEP 621 metadata for package `devlog` (src layout, `requires-python = ">=3.11"`), runtime dependency `typer>=0.12,<1.0`, optional-dependencies group `dev = ["pytest>=8,<9"]`, console script `devlog = "devlog.cli:app"`, and `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = ["src"]`
- [ ] T002 [P] Create `src/devlog/__init__.py` exposing `__version__ = "0.1.0"` and `src/devlog/__main__.py` delegating to `devlog.cli.app` so `python -m devlog` works
- [ ] T003 [P] Create `src/devlog/services/__init__.py` and the `src/devlog/` and `tests/` package directories so the layout from plan.md exists
- [ ] T004 [P] Create `.gitignore` at the repository root excluding `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.egg-info/`, `dist/`, `build/`, and `*.db`
- [ ] T005 [P] Create `README.md` (Spanish) with the install steps, the four commands (`add`, `list`, `search`, `export`), the store location `~/.devlog/notes.db`, the `DEVLOG_DB_PATH` override, and the exit codes
- [ ] T006 Obtain explicit user approval for the dependency set documented in `research.md` R14 (Constitution Principle IV), then bootstrap with `uv venv && uv pip install -e ".[dev]"` and verify `devlog --help` prints the Spanish help text

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create `src/devlog/config.py` with the store path resolution — `DEVLOG_DB_PATH` when set, otherwise `Path.home() / ".devlog" / "notes.db"` — plus the exit-code constants (SUCCESS `0`, ERROR `1`, USAGE `2`, NO_RESULTS `3`), the default export filename `devlog-notes.md`, the default export directory `.`, and the SQLite `busy_timeout` of `5000` ms
- [ ] T008 Create `src/devlog/errors.py` with the exception hierarchy that maps to exit codes and carries only Spanish user-facing messages (FR-020, no stack traces): `DevLogError` (base, exit `1`), `StoreError` (store cannot be opened or is corrupted), `StoreLockedError` (another operation holds the lock), `ExportPathError` (destination missing or unwritable), `ValidationError` (exit `2`), and `NoResultsError` (exit `3`)
- [ ] T009 Create `src/devlog/db.py` with the connection factory — open the SQLite file applying `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000` — creating the parent directory with mode `0o700` when missing, and `ensure_schema()` executing ONLY the statements from `data-model.md` (notes, tags, note_tags with `PRIMARY KEY (note_id, tag_id)`, plus `idx_notes_created_at` and `idx_note_tags_tag`), all with `CREATE TABLE IF NOT EXISTS`; the module MUST NOT contain `DROP`, `TRUNCATE`, `DELETE`, `ALTER`, or any reset routine (Constitution Principle II, FR-019), and a corrupted file MUST raise `StoreError` without modifying the file (research.md R10)
- [ ] T010 Create `src/devlog/models.py` with the dataclasses from `data-model.md`: `Note(id, title, content, created_at)` — `title` mandatory and "not empty and does not consist solely of spaces", `content` optional defaulting to empty, `created_at` an immutable UTC ISO-8601 timestamp; `Tag(id, name, created_at)` — `name` unique and stored trimmed and lowercased; `ExportResult(path, note_count, generated_at)`
- [ ] T011 Create `src/devlog/formatting.py` with `normalize_tag(name)` (trim + lowercase), `split_tags(values)` (split on commas, trim, lowercase, discard empty values, deduplicate preserving order), `format_local_datetime(iso_utc)` (local time as `YYYY-MM-DD HH:MM`), `format_tag_list(tags)` (comma-separated, `(sin etiquetas)` when empty) and `format_note_line(note)` producing exactly `#<id>  <YYYY-MM-DD HH:MM>  <tags>  <title>` with the title last so it is never truncated (FR-008, research.md R13)
- [ ] T012 Create `src/devlog/repository.py` with parameterised SQL only: `insert_note(conn, title, content, tags)` inserting the note and its tag links in one transaction and reusing an existing tag row for a repeated normalised name, `list_notes(conn)` ordered by `created_at DESC, id DESC`, `search_notes_by_tags(conn, tags)` matching tags EXACTLY against the normalised name and requiring EVERY requested tag (AND, via `GROUP BY` + `HAVING COUNT(DISTINCT name) = ?`), `count_notes(conn)` and `get_tags_for_note(conn, note_id)`
- [ ] T013 Create `tests/conftest.py` with the fixtures `tmp_store` (a throwaway SQLite file inside `tmp_path`), `isolated_store` (monkeypatching `DEVLOG_DB_PATH` to that file), `runner` (`typer.testing.CliRunner`) and `seed_notes` (inserts N notes with given dates and tags), guaranteeing that no test ever reads or writes `~/.devlog/notes.db` (Constitution Principle I, Safety)
- [ ] T014 [P] Create `tests/test_repository.py` covering the storage layer: insert and read back a note, a note with no tags, reuse of one tag row across notes, the `note_tags` primary key rejecting a duplicate tag inside the same note, newest-first ordering with the `id` tiebreak for same-second notes, `search_notes_by_tags` returning only notes carrying EVERY requested tag, and a corrupted store (a file containing non-database bytes) raising `StoreError` while leaving the file byte-for-byte unchanged
- [ ] T015 [P] Create `tests/test_formatting.py` covering the pure formatting units: tag trimming and lowercasing, comma-splitting and de-duplication, empty tag values discarded, local date rendering, and the exact `#<id>  <date>  <tags>  <title>` line shape

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Save a development note (Priority: P1) 🎯 MVP

**Goal**: A developer records a note from the terminal with a title, optional content, and tags, and is certain it is permanently saved.

**Independent Test**: Create a note with a title, content, and tags, then confirm it is retrievable from the store's listing query (`repository.list_notes`) and that it survives a new process invocation (FR-004). The user-facing `devlog list` command is delivered by Phase 4 (US2); US1's own test asserts persistence through the foundational listing query so this story stays independently deliverable.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US1] Create `tests/test_cli_add.py` covering the success path (confirmation `Nota #<id> guardada (<YYYY-MM-DD HH:MM>).` plus `Etiquetas: bug, api`; a title-only note saved with empty content and no tags; the `Etiquetas:` line omitted when there are no tags; the note persisted across two separate invocations), the validation path (an empty or whitespace-only title produces `El título no puede estar vacío.` and exit code `2` with nothing saved), the input paths (`--content`, `--content-file PATH`, `--content-file -` reading multi-line content from stdin with its line breaks preserved), the tag rules (repeats and case differences collapse into one normalised tag, whitespace is trimmed, empty tags are discarded) and the operational-error path (a corrupted store produces the Spanish `StoreError` message and exit code `1` with no traceback)

### Implementation for User Story 1

- [ ] T017 [US1] Create `src/devlog/services/note_service.py` with `create_note(title, content, tags)` — reject a title that "is not empty and does not consist solely of spaces" with `ValidationError` (exit `2`), normalise the tags, write the note plus its tag links in a single transaction, and return the created `Note`
- [ ] T018 [US1] Implement the `add` command in `src/devlog/cli.py` — Typer app plus `devlog add` with the positional `TITLE` and the options `--title`, `--content/-c`, `--content-file PATH` (`-` meaning stdin) and `--tag/-t` (repeatable, comma-separated values split); when no content option is given and stdin is not a terminal, read the body from stdin; print the Spanish confirmation and map `ValidationError` → exit `2` and `StoreError`/`StoreLockedError` → exit `1` per `contracts/cli.md` §2
- [ ] T019 [US1] Verify User Story 1 independently: run `pytest tests/test_cli_add.py -q` and the `devlog add` scenarios from `quickstart.md` §4 against a temporary `DEVLOG_DB_PATH`, confirming the note is saved, validated, and persisted

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - View my notes (Priority: P2)

**Goal**: A developer sees every saved note with its title, date, and tags, newest first, in one listing.

**Independent Test**: Create several notes with different dates and run `devlog list`; it must return all of them ordered from newest to oldest with the title, creation date, and tags visible.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T020 [P] [US2] Create `tests/test_cli_list.py` covering the success path (three notes with different dates all appear, newest first, each showing title, creation date, and tags in the `#<id>  <date>  <tags>  <title>` shape), the empty-state path (an empty store prints `No hay notas guardadas todavía.` with exit code `0` and no error output), the untagged path (a note without tags still appears showing `(sin etiquetas)`) and completeness (500 seeded notes produce exactly 500 lines, every id present, no duplicates — SC-003)

### Implementation for User Story 2

- [ ] T021 [US2] Implement the `list` command in `src/devlog/cli.py` — call `repository.list_notes`, render each note with `formatting.format_note_line` ordered `created_at DESC, id DESC` (FR-007), print `No hay notas guardadas todavía.` when the store is empty, and exit `0` in both cases
- [ ] T022 [US2] Verify User Story 2 independently: run `pytest tests/test_cli_list.py -q` and the `devlog list` scenarios from `quickstart.md` §5, confirming ordering, the empty state, and the 500-note completeness check

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Search notes by tag (Priority: P3)

**Goal**: A developer filters notes by one or more tags and retrieves the relevant ones in seconds.

**Independent Test**: Create notes with different tag combinations and run `devlog search`; it must return exactly the notes matching the requested tag and no others.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T023 [P] [US3] Create `tests/test_cli_search.py` covering the success path (searching `bug` returns only the notes carrying that tag, each line showing title, date, and tags), the AND rule (a note is returned only when it carries EVERY requested tag; a note missing one of them is excluded), the normalisation rule (`Bug`, ` bug ` and `bug` select the same notes), and the no-matches path (an unknown tag prints `No se encontraron notas con esas etiquetas.` and exits with code `3`, clearly distinguished from an error)

### Implementation for User Story 3

- [ ] T024 [US3] Create `src/devlog/services/search_service.py` with `search_by_tags(tags)` — normalise the requested tags with `formatting.normalize_tag`, require at least one tag, call `repository.search_notes_by_tags` (exact match, AND semantics) and return the ordered notes
- [ ] T025 [US3] Implement the `search` command in `src/devlog/cli.py` — accept one or more tag arguments (repeatable and comma-separated), print the matching notes with `formatting.format_note_line`, print `No se encontraron notas con esas etiquetas.` and exit with code `3` when nothing matches, and exit `2` when no tag is supplied
- [ ] T026 [US3] Verify User Story 3 independently: run `pytest tests/test_cli_search.py -q` and the `devlog search` scenarios from `quickstart.md` §6, confirming the AND behaviour and the exit code `3`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Export my notes to Markdown (Priority: P4)

**Goal**: A developer exports every note to a readable Markdown file to review, version, or publish it.

**Independent Test**: Export a known set of notes and verify the generated Markdown file contains each note with its title, date, tags, and content, without losing information.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T027 [P] [US4] Create `tests/test_markdown.py` covering the document layout from `contracts/markdown-export.md` (H1 `Notas de DevLog`, the generation line with the note count, one `## #<id> · <title>` section per note, the `- **Creado**:` and `- **Etiquetas**:` metadata lines, `---` separators), the body written VERBATIM byte-for-byte including line breaks, lists, quotes, and Markdown characters (FR-018, SC-006), the title escaping of the characters `\ ` * _ { } [ ] ( ) # + - . ! | < >`, the longer fence when the body contains a run of three or more backticks, and the valid empty document for a store with no notes
- [ ] T028 [P] [US4] Create `tests/test_cli_export.py` covering the success path (the file contains every note with title, date, tags, and content; the default destination is `devlog-notes.md` and `--output PATH` is honoured), the overwrite path (an existing file triggers the confirmation prompt `El archivo ya existe: <ruta>. ¿Quieres sobrescribirlo? [s/N]`, declining leaves the file untouched, `--force` replaces it without asking, and a non-interactive run without `--force` refuses with exit code `1` and leaves the file untouched), the error paths (a missing parent directory reports `No existe el directorio de destino: <dir>.` with exit code `1` and leaves no partial file; an unwritable destination reports `No se pudo escribir el archivo: <ruta>.`) and the empty-store path (a valid empty Markdown file plus `No había notas para exportar.`)

### Implementation for User Story 4

- [ ] T029 [US4] Create `src/devlog/markdown.py` with `render_document(notes, generated_at)` producing exactly the layout in `contracts/markdown-export.md`, `escape_title(title)` applying the documented backslash escapes, and `fence_body(body)` adding a longer fence ONLY when the body contains a line of three or more backticks
- [ ] T030 [US4] Create `src/devlog/services/export_service.py` with `export_notes(destination, force)` — resolve the destination to `devlog-notes.md` in the current directory by default, apply the overwrite policy (prompt for confirmation, replace with an explicit `--force`, or refuse with `ExportPathError` when the session is non-interactive and `--force` was not given), render the document and write it atomically (write to a temporary file in the destination directory, then replace) so a failure leaves NO partial file behind, and return an `ExportResult`
- [ ] T031 [US4] Implement the `export` command in `src/devlog/cli.py` with the options `--output/-o` and `--force`, the Spanish confirmation `Notas exportadas a <ruta> (<n> notas).`, and the exit codes from `contracts/cli.md` §5
- [ ] T032 [US4] Verify User Story 4 independently: run `pytest tests/test_cli_export.py tests/test_markdown.py -q` and the `devlog export` scenarios from `quickstart.md` §7, confirming content fidelity, the overwrite policy, and the error paths

**Checkpoint**: All four user stories are independently functional — the feature is complete

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Create `tests/test_performance.py` verifying that listing 500 notes completes in under 3 seconds (SC-004) and that exporting 500 notes yields a file containing 100% of the notes with title, date, tags, and content and no character corruption (SC-006)
- [ ] T034 [P] Update `README.md` with the final command reference, the exit-code table, the store location and the `DEVLOG_DB_PATH` override, and a sample of the exported Markdown format
- [ ] T035 [P] Verify the dependency set in `pyproject.toml` and the lockfile against `research.md` R14: only `typer` (with `click`, `typing-extensions`, `shellingham`, `rich`) at runtime and `pytest` (with `pluggy`, `iniconfig`, `packaging`) for development, each pinned to a specific version, with no ORM, HTTP client, migration framework, or date library present (Constitution Principle IV, FR-025)
- [ ] T036 Run the complete suite with `pytest -q` over `tests/` and confirm every test passes with no network access and no writes outside the temporary stores (SC-008, FR-024, Constitution Principle I)
- [ ] T037 Run the full validation from `quickstart.md` §2–§12 against a temporary `DEVLOG_DB_PATH` and record the evidence for each scenario, including the corrupted-store scenario that MUST leave the file untouched
- [ ] T038 Perform the final constitution gate review — record the evidence for each of the six gates in `specs/001-devlog-cli/plan.md` (Constitution Check table) and in `specs/001-devlog-cli/quickstart.md`, confirm that ZERO destructive store operations were executed without recorded explicit approval, and commit the change with a message describing the task it completes (Constitution Principle III, Safety, Governance)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses the foundational `repository.list_notes`; independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses the foundational tag normalisation; independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Uses the foundational `repository.list_notes`; independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before commands
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch the US1 test task with the US1 service and command tasks in sequence:
Task: "Create tests/test_cli_add.py"
Task: "Create src/devlog/services/note_service.py"
Task: "Implement the add command in src/devlog/cli.py"

# Launch the Foundational unit tests together (different files):
Task: "Create tests/test_repository.py"
Task: "Create tests/test_formatting.py"
```

---

## Parallel Example: User Story 4

```bash
# Launch both US4 test modules together (different files):
Task: "Create tests/test_markdown.py"
Task: "Create tests/test_cli_export.py"

# Launch the US4 implementation modules together (different files):
Task: "Create src/devlog/markdown.py"
Task: "Create src/devlog/services/export_service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constitution Principle III applies**: work one task at a time, in the order given, and stop for user review after each one
- **Constitution Principle II applies**: no `DROP`, `TRUNCATE`, `DELETE`, schema reset, or store recreation may be executed during any task without the user's explicit approval for that specific operation, stated immediately before it runs
- **Constitution Principle IV applies**: T006 installs the dependencies; no other task may add a package

# Implementation Plan: DevLog CLI

**Branch**: `001-devlog-cli` | **Date**: 2026-10-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-devlog-cli/spec.md`, tech direction supplied by the user: Python + Typer + SQLite.

**Note**: This document was filled in by the `/speckit.plan` command. The three
`[NEEDS CLARIFICATION]` markers that were present in `spec.md` (FR-003, FR-010, FR-012)
were resolved on 2026-10-21 — the store location was confirmed by the user as a single
file under the home directory (Option A) — and are now folded into `spec.md` and recorded
in its `## Clarifications` section. See `research.md` for the decision log.

## Summary

DevLog CLI is a single-user, offline terminal notebook that stores development notes in a
local SQLite file. It supports exactly four capabilities — create a note, list notes,
search notes by tag, and export notes to Markdown — with no authentication, no GUI, and no
network access.

The technical approach is a single Python package (`devlog`) using **Typer** for the
command surface, the **standard-library `sqlite3`** module for persistence (no ORM, no
migration framework), and **pytest** with `typer.testing.CliRunner` for the automated
tests required by Constitution Principle I. The storage layer is deliberately thin — one
repository module issuing parameterised SQL — because the domain has a single entity
graph (Note, Tag, Note-Tag) and a bounded data volume (reference dataset of 500 notes).

The design decisions that the spec left open are recorded in `research.md`; the two that
most shape the implementation are:

- the store is a single file at `~/.devlog/notes.db` (overridable via `DEVLOG_DB_PATH`),
  never deleted or reset automatically (FR-003, Constitution Principle II);
- tag search uses **exact** matching on the normalised tag with **AND** semantics for
  multiple tags (FR-010).

## Technical Context

**Language/Version**: Python 3.11+ (validated locally against the system interpreter, currently 3.14.7)

**Primary Dependencies**: `typer` (pinned `==0.27.3`) + standard-library `sqlite3` (no database driver, no ORM, no migration library)

**Transitive Dependencies (disclosed per Constitution Principle IV)**: `annotated-doc`, `shellingham`, `rich` (+ `markdown-it-py`, `mdurl`, `pygments`) from `typer`; `iniconfig`, `packaging`, `pluggy` from `pytest` (development only). Recorded with exact versions in `uv.lock`

**Storage**: SQLite file at `~/.devlog/notes.db` (overridable with the `DEVLOG_DB_PATH` environment variable), WAL journal mode, `foreign_keys=ON`, `busy_timeout=5000` ms; schema created additively with `CREATE TABLE IF NOT EXISTS`

**Testing**: `pytest` (dev dependency) + `typer.testing.CliRunner` for end-to-end command tests; each test points at a throwaway SQLite file in a temporary directory so the developer's real store is never touched

**Target Platform**: Linux and macOS terminals with Python 3.11+; fully offline; no network calls, no GUI, no editor integration

**Project Type**: single-package command-line application (`cli`)

**Performance Goals**: listing 500 notes completes in under 3 seconds (SC-004); creating a note completes in under 1 second; a tag search over 500 notes completes in under 1 second; exporting 500 notes completes in under 5 seconds (SC-006)

**Constraints**: single local actor; offline only (FR-023); no authentication (FR-022); Spanish user-facing language; zero destructive store operations outside explicit user consent (FR-019, Constitution Principle II); no third-party dependency without recorded justification (FR-025, Constitution Principle IV); spec-only scope — no editing, no deleting, no free-text search, no alternative export formats (Constitution Principle V)

**Scale/Scope**: one user, one local store, four commands, reference dataset of 500 notes (SC-003/SC-004/SC-006)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate (from `constitution.md`) | How this plan satisfies it | Status at plan time |
|---|---|---|---|
| I | Test coverage for every endpoint, covering success + validation/authorization failure + server-error path; deterministic, no live network; test lands with the code | The four commands are the "endpoints". `tests/` contains one module per command (success, validation failure, operational-error path) plus unit tests for normalisation, Markdown rendering, and the repository. All tests use a temporary SQLite file via `DEVLOG_DB_PATH`; no network, no live services | PASS (design; must be honoured per task) |
| II | No destructive database operations without explicit per-operation user approval | The only schema operation is `CREATE TABLE IF NOT EXISTS` (additive). The tool never issues `DROP`, `TRUNCATE`, `DELETE`, `ALTER`, or reset; a corrupted store produces an error and the file is left untouched (R10); export overwrite requires a confirmation prompt or an explicit `--force` (R4) | PASS |
| III | One task at a time, stop for review after each | Task breakdown is produced later by `/speckit.tasks`; each task in this plan is independently reviewable and ends with tests + evidence | PASS (process rule for `/speckit.tasks` and implementation) |
| IV | No new dependency without recorded justification, approval, and version pinning | Dependency set is deliberately minimal and justified in `research.md` R14: `typer` (+ `annotated-doc`, `shellingham`, `rich` and its own transitive packages) and `pytest` (+ `iniconfig`, `packaging`, `pluggy`, dev-only). `sqlite3`, `datetime`, `pathlib`, `tempfile` come from the standard library. No ORM, no HTTP client, no migration tool | PASS (dependencies approved and pinned in `pyproject.toml` + `uv.lock`) |
| V | Spec-only minimal scope | Exactly the four specified capabilities are designed. Editing, deleting, free-text search, categories, attachments, cloud sync, extra export formats, JSON output, and machine-readable modes are all excluded (R3, R13 in `research.md`; "Out-of-scope functionality for v1" in the spec Assumptions) | PASS |
| Safety | Environment targeting; non-destructive verification; tests must not mutate the developer database | Tests run against `tmp_path` databases; schema verification happens against a throwaway file, never the user's store; no command targets a remote or shared database | PASS |
| Workflow | Spec Kit sequence specify → clarify → plan → tasks → implement; each task ends with a review stop and a list of verified gates | This plan is the `plan` stage artifact. The spec's three clarification markers were resolved on 2026-10-21, folded into `spec.md` (FR-003, FR-010, FR-012) and recorded in its `## Clarifications` section | PASS |
| Governance | Constitution prevails over plan, task list, or prompt | The user's stated stack (Python/Typer/SQLite) is compatible with every principle; no conflict found. Principle V blocks any interpretation of "note management" that would add edit/delete | PASS |

**Complexity Tracking**: no violations to justify — the plan adds no fourth project, no
pattern, and no dependency beyond the justified set. The table is intentionally omitted.

## Project Structure

### Documentation (this feature)

```text
specs/001-devlog-cli/
├── plan.md                    # This file (/speckit.plan output)
├── spec.md                    # Feature specification (input, needs the three markers folded in)
├── research.md                # Phase 0 output — decisions R1..R15, spec sync list
├── data-model.md              # Phase 1 output — Note, Tag, Note-Tag, Export Result
├── quickstart.md              # Phase 1 output — runnable end-to-end validation guide
├── contracts/
│   ├── cli.md                 # Phase 1 output — command, flag, exit-code, and message contract
│   └── markdown-export.md     # Phase 1 output — exported Markdown file format contract
├── checklists/
│   └── requirements.md        # Specification quality checklist
└── tasks.md                   # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
pyproject.toml                 # packaging, pinned deps, `devlog` entry point, pytest config
README.md                      # install + usage (user-facing, Spanish)
src/devlog/
├── __init__.py                # package version (__version__)
├── __main__.py                # `python -m devlog` entry point
├── cli.py                     # Typer app + the four commands (add/list/search/export)
├── config.py                  # store path resolution, env vars, exit codes, defaults
├── db.py                      # connection factory, pragmas, additive schema creation
├── errors.py                  # domain exceptions -> exit codes + Spanish messages
├── models.py                  # Note, Tag, ExportResult dataclasses
├── repository.py              # SQL only: create/list/search-by-tags/count queries
├── services/
│   ├── note_service.py        # create/list orchestration + validation
│   ├── search_service.py      # tag matching (exact + AND), result shaping
│   └── export_service.py      # Markdown rendering + destination/overwrite policy
├── markdown.py                # Markdown document builder + escaping rules
└── formatting.py              # date and tag display formatting
tests/
├── conftest.py                # tmp SQLite fixture, DEVLOG_DB_PATH isolation, seeded helpers
├── test_cli_add.py            # US1: success, empty title, multi-line content, tag normalisation
├── test_cli_list.py           # US2: ordering, empty state, untagged note, 500-note completeness
├── test_cli_search.py         # US3: exact match, AND semantics, no matches -> exit 3
├── test_cli_export.py         # US4: content fidelity, overwrite prompt, --force, bad path
├── test_repository.py         # storage layer, WAL/busy behaviour, uniqueness constraints
├── test_formatting.py         # tag normalisation, date rendering, note line shape
├── test_markdown.py           # escaping rules and byte-for-byte content preservation
└── test_performance.py        # SC-004/SC-006 timing checks over 500 notes
```

**Structure Decision**: a single `src/`-layout package plus a flat `tests/` directory. The
tool has one process, one store, and four commands, so a modular-monorepo or layered
multi-package layout would add navigation cost without removing any real complexity. The
internal split (`db` → `repository` → `services` → `cli`) keeps the SQL out of the command
layer so the command layer stays testable through `CliRunner` and the storage layer stays
testable on its own.

## Phase Boundaries (for `/speckit.tasks`)

1. **Packaging and bootstrap** — `pyproject.toml`, `uv`/venv bootstrap, `devlog` entry point.
2. **Storage foundation** — `db.py`, `repository.py`, additive schema, `config.py`.
3. **Note creation** — `note_service.py` + `devlog add` + validation.
4. **Listing** — `devlog list` with newest-first ordering and the empty state.
5. **Tag search** — `search_service.py` + `devlog search` (exact, AND) + exit code 3.
6. **Markdown export** — `markdown.py`, `export_service.py`, `devlog export` + overwrite policy.
7. **Error handling and exit codes** — `errors.py`, corrupted store, unwritable destination.
8. **Test suite completion and performance checks** — one module per command, 500-note checks.

Each phase lands with its own tests and evidence, in this order, one review stop per phase
(Constitution Principle III).

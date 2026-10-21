# Phase 0 Research: DevLog CLI

**Feature**: `001-devlog-cli` | **Date**: 2026-10-21 | **Inputs**: `spec.md`,
`constitution.md`, user direction "Using Python with Typer and SQLite".

**Canonical path**: `specs/001-devlog-cli/research.md`

This document resolves every `[NEEDS CLARIFICATION]` marker in the specification and
records the remaining design decisions that the plan depends on. Each entry follows the
required format: Decision / Rationale / Alternatives considered.

## Open Items Resolved From the Specification

### R1 — Where the SQLite store lives and how its lifecycle is governed (resolves FR-003)

- **Decision**: One single store file at `~/.devlog/notes.db`, resolved from the user's
  home directory. The path can be overridden with the `DEVLOG_DB_PATH` environment
  variable (used by the test suite and by users who want an isolated notebook). The
  containing directory is created on demand with owner-only permissions. The schema is
  created with `CREATE TABLE IF NOT EXISTS` and future changes use additive
  `ALTER TABLE ... ADD COLUMN` migrations only. The tool never deletes, resets, moves, or
  recreates an existing store, and never asks for approval to do so because it never
  performs such an operation.
  *(Confirmed by the user on 2026-10-21: Option A — one single fixed file under the
  home directory, the same store from any working folder.)*
- **Rationale**: A personal development notebook should be in one predictable place and
  reachable from any directory; a store tied to the working directory would scatter notes
  across project folders and quietly hide them from the user (US2 expects "all my notes").
  The environment override is the cheapest possible seam for the Constitution's
  requirement that tests never mutate the developer's real database.
- **Alternatives considered**: (a) `./.devlog/notes.db` in the current directory —
  rejected, notes get fragmented per project and the user loses sight of them;
  (b) XDG data directory (`~/.local/share/devlog/notes.db`) — technically more idiomatic on
  Linux but less discoverable for a non-expert user; it remains a future, additive
  change of the default path; (c) an explicit `--db` flag on every command — rejected as
  noise on the command line and an invitation to point the tool at the wrong file.
- **Spec impact**: closes FR-003; supports FR-004 and SC-007; resolves the "first use"
  and "corrupted store" edge cases.

### R2 — Tag matching semantics (resolves FR-010)

- **Decision**: Tag matching is **exact** against the normalised tag value (trimmed and
  lowercased). When several tags are requested, a note is returned only if it carries
  **every** requested tag (AND). Substring matching and OR-matching are not part of v1.
- **Rationale**: Tags are a normalised, closed vocabulary (FR-017), so substring matching
  would return notes for `api` when the user asked for `apiary`, breaking the "exactly
  the notes matching the requested tag" promise in US3 and the correctness claim in
  SC-005. AND keeps search a narrowing filter, which is the intent stated in the US3
  story ("filter my notes by one or more tags"). Both alternatives remain a purely
  additive change later (an explicit opt-in flag).
- **Alternatives considered**: (a) substring/prefix matching — rejected, produces false
  positives and contradicts the exact-match reading of the spec; (b) OR semantics —
  rejected, it widens rather than narrows the result set and contradicts the filtering
  framing; (c) case-sensitive matching — rejected, FR-017 mandates case normalisation.
- **Spec impact**: closes FR-010; fixes the SC-005 verification rule.

### R3 — Scope of note management (resolves FR-012)

- **Decision**: v1 covers exactly four capabilities — create, list, search by tags, and
  export to Markdown. Editing and deleting existing notes are **out of scope for v1**,
  matching the "Out-of-scope functionality for v1" list already published in the spec's
  Assumptions section. Adding them requires an explicit scope expansion.
- **Rationale**: The Assumptions section and FR-012 contradicted each other; the
  Assumptions list is the more specific and deliberate statement, and Constitution
  Principle V forbids shipping behaviour that is not written in the approved spec.
  Editing/deleting would also require new user stories, acceptance scenarios, and
  decisions about what "delete" means for a store that must never be destructively
  modified.
- **Alternatives considered**: (a) including edit and delete in v1 — rejected, it is a
  scope expansion that would need its own specification approval; (b) a read-only
  "soft delete" flag — rejected, same reason and it adds a lifecycle state the spec does
  not describe.
- **Spec impact**: closes FR-012; confirms the out-of-scope list.

## Design Decisions Required by the Plan

### R4 — Export destination and overwrite consent

- **Decision**: Default destination is `./devlog-notes.md` in the current directory;
  `--output/-o PATH` selects another path. If the destination already exists, the tool
  asks for confirmation in Spanish before replacing it. `--force` replaces the file
  without prompting — that flag is an explicit user instruction given at that moment. In
  a non-interactive session (stdin is not a TTY) without `--force`, the tool refuses with
  a clear message and never overwrites.
- **Rationale**: FR-014 requires the user to be able to choose the destination, and
  FR-015 forbids overwriting without explicit confirmation. A deterministic default keeps
  the command runnable with no arguments; the non-interactive refusal is the only way to
  honour "confirmation at that moment" without a prompt that no one can answer.
- **Alternatives considered**: (a) always prompting even with `--force` — rejected,
  `--force` would be meaningless; (b) timestamped default filename — rejected, it makes
  scripting and re-export unpredictable; (c) failing when the file exists — rejected,
  it removes the confirmation path the spec explicitly asks for.

### R5 — Exit codes

- **Decision**: `0` success (including an empty listing and a successful export), `1`
  operational error (store failure, corrupted database, unwritable destination, lock
  contention), `2` usage or validation error (Typer's standard code for bad arguments,
  also used for an empty title), `3` no results (a tag search that matched nothing).
- **Rationale**: FR-021 requires distinguishing success, absence of results, and error.
  Reusing `2` for usage errors keeps Typer's built-in convention instead of inventing a
  second usage code, and `3` gives "nothing found" a dedicated, script-friendly value.
- **Alternatives considered**: (a) only `0` and `1` — rejected, FR-021 explicitly asks
  for three distinguishable outcomes; (b) a negative code for "no results" — rejected,
  shell conventions treat any non-zero as failure and would misreport an expected outcome.

### R6 — How a note's title, content, and tags are supplied

- **Decision**: `devlog add "<title>"` takes the title as a positional argument (also
  accepted as `--title`); `--content/-c` carries inline text; `--content-file PATH`
  reads the body from a file, and `--content-file -` reads it from standard input, which
  is how multi-line bodies are entered; `--tag/-t` is repeatable. When neither
  `--content` nor `--content-file` is given and stdin is not a TTY, stdin is read as the
  body. Tags may also be given comma-separated within one `--tag` value and are split.
- **Rationale**: FR-018 requires line breaks to survive verbatim, and command-line
  arguments cannot carry a multi-line body reliably; the stdin seam makes
  `pbpaste | devlog add "Title" --content-file -` work. Plain flags keep the command
  scriptable, which the exit-code contract depends on.
- **Alternatives considered**: (a) fully interactive prompts — rejected, they block
  scripted use and add an extra UI surface the spec never describes; (b) editor
  integration — rejected, explicitly out of scope in the Assumptions; (c) a body argument
  only — rejected, it cannot represent multi-line content.

### R7 — Timestamp storage and display

- **Decision**: `created_at` is stored as UTC ISO-8601 (`YYYY-MM-DDTHH:MM:SSZ`) and
  rendered to the user in local time as `YYYY-MM-DD HH:MM`. The listing and search
  results are ordered by `created_at DESC, id DESC`, so notes created in the same second
  still have a deterministic order.
- **Rationale**: UTC storage stays stable across daylight-saving and timezone changes;
  the local display matches the spec's "readable local format with year, month, day, hour,
  and minutes". The `id` tiebreak makes SC-003's "without omissions or duplicates" and
  SC-005's ordering deterministic and therefore testable.
- **Alternatives considered**: (a) storing local time — rejected, ambiguous across
  timezone changes; (b) Unix epoch integers — rejected, less readable when inspecting the
  file by hand; (c) ordering by `id` only — rejected, ids are not reliable chronological
  proxies.

### R8 — Markdown export format and escaping

- **Decision**: The exported file is a single H1 title, one generation-timestamp line,
  then one H2 section per note (`## #<id> · <title>`) followed by a metadata line with
  the creation date and the tags, then the body. The body is written **verbatim** — no
  escaping — so line breaks, lists, and special characters survive byte-for-byte
  (FR-018, SC-006). Only two controlled transformations are applied: the note title has
  its Markdown control characters escaped so a title can never break the document
  structure, and a body containing a line of three or more backticks is wrapped in a
  longer fence so it cannot terminate a block early.
- **Rationale**: FR-018 asks for two things at once — content preserved intact and
  rendered safely. Escaping the body would break "intact"; leaving the title unescaped
  would break the structure. Escaping only the title and fencing only pathological
  bodies satisfies both, and keeps SC-006 verifiable by comparing the extracted body with
  the original byte-for-byte.
- **Alternatives considered**: (a) escaping the whole body — rejected, it corrupts the
  user's text and violates the byte-fidelity criterion; (b) HTML-escaping the body —
  rejected, it is lossy and unreadable; (c) putting the body in a code fence always —
  rejected, it destroys the readability of lists and formatting that the spec explicitly
  wants preserved. The exact layout is specified in `contracts/markdown-export.md`.

### R9 — Concurrency and concurrent writes

- **Decision**: The store is opened in WAL journal mode with `busy_timeout=5000` ms and
  `foreign_keys=ON`. A concurrent writer waits up to five seconds for the lock; if it
  still cannot proceed, the operation fails with a clear Spanish message and exit code 1,
  and no data is lost or partially written.
- **Rationale**: The spec's edge case requires that two simultaneous operations do not
  corrupt the store and that the second one is told clearly what happened. WAL plus a
  busy timeout is the standard SQLite answer and needs no extra dependency.
- **Alternatives considered**: (a) failing immediately on a locked database — rejected, it
  would make routine parallel use flaky; (b) a separate lock-file protocol — rejected,
  it duplicates a mechanism SQLite already provides; (c) an application-level lock file —
  rejected, same reason plus it adds failure modes.

### R10 — Corrupted or unreadable store

- **Decision**: Storage failures are caught at the database boundary and reported as a
  clear Spanish message that explains that the file may be damaged and asks the user to
  restore a backup or move the file aside manually. The tool exits with code 1 and never
  deletes, moves, renames, or recreates the store.
- **Rationale**: Constitution Principle II and the spec's own edge case require the tool
  to leave the data intact and never reset it silently. The tool must not destroy the
  only copy of the user's notes in order to recover from a read error.
- **Alternatives considered**: (a) automatically recreating an empty store — rejected, it
  destroys the user's data; (b) a "repair" routine — rejected, it is a destructive
  operation needing explicit approval and is out of scope; (c) a raw stack trace —
  rejected, FR-020 forbids technical traces.

### R11 — Note identity

- **Decision**: A note is identified by an integer `id` assigned by the store, displayed
  as `#<id>`, stable for the life of the note (FR-002). No UUIDs.
- **Rationale**: A short, human-typeable identifier is more useful in a terminal notebook
  and needs no extra column; integer primary keys are monotonic and deterministic in
  tests. The spec requires a unique identifier, not a particular format.
- **Alternatives considered**: (a) UUID text — rejected, longer and less readable for
  single-user local use; (b) title as the identifier — rejected, titles are editable in
  principle and not guaranteed unique; (c) a compound natural key — rejected, fragile.

### R12 — Tag storage model

- **Decision**: A `tags` table (`id`, unique `name`, `created_at`) joined to `notes` by a
  `note_tags` table whose primary key is `(note_id, tag_id)`. Tag names are trimmed and
  lowercased before being written, so the unique constraint on `name` also provides
  case-insensitive uniqueness. The composite primary key makes a duplicate tag inside a
  single note impossible at the database level (FR-017).
- **Rationale**: The many-to-many relation is the actual domain shape; enforcing
  uniqueness structurally removes an entire class of bugs instead of relying on
  application checks.
- **Alternatives considered**: (a) a comma-separated column on `notes` — rejected, it
  cannot enforce uniqueness or support indexed tag queries; (b) a JSON column — rejected,
  same limitations without relational guarantees; (c) duplicating tag names on every note
  — rejected, it breaks uniqueness across notes.

### R13 — Listing output format

- **Decision**: The listing and the search results are rendered as plain text lines, one
  note per line, in the form `#<id>  <YYYY-MM-DD HH:MM>  <tags>  <title>`, with the tags
  shown as a comma-separated list in brackets or `(sin etiquetas)` when the note has none,
  and the title last so it is never truncated. No table, no colour, no pagination.
- **Rationale**: A plain line format is deterministic, greppable, pipe-friendly, and cheap
  to render for 500 notes, which directly protects the SC-003 completeness check and the
  SC-004 timing budget. It also keeps automated assertions reliable: a formatted table
  would wrap long titles across lines and break "the title appears in the output"
  assertions.
- **Alternatives considered**: (a) a Rich table — rejected, wrapping and width handling
  make output and tests brittle for no user-visible gain; (b) a paginated list — rejected,
  it adds a page-size decision the spec never asks for and complicates "100% of notes
  appear"; (c) JSON output — rejected, out of scope for v1.

### R14 — Dependency set and justification (Constitution Principle IV)

- **Decision**: Runtime dependency: `typer` (pinned `typer==0.27.3`), which transitively
  installs `annotated-doc` 0.0.5, `shellingham` 1.5.4 and `rich` 15.0.0 (which in turn
  brings `markdown-it-py` 4.2.0, `mdurl` 0.1.2 and `pygments` 2.21.0). Development
  dependency: `pytest` (pinned `pytest==8.4.2`), which transitively installs
  `iniconfig` 2.3.1, `packaging` 26.3, `pluggy` 1.7.0 and `pygments` 2.21.0.
  Everything else comes from the standard library: `sqlite3` for storage, `datetime`
  for timestamps, `pathlib` for paths, `tempfile` for the atomic write, and plain
  string handling for tag normalisation. Explicitly **not** used: ORM or query
  builders, HTTP clients, migration frameworks, date/time libraries, logging
  frameworks, and packaging tools beyond `uv`/`venv`.
  *Update of 2026-10-21 (during implementation):* the set originally assumed
  `click` and `typing-extensions` would come with `typer`. The installed
  `typer 0.27.3` no longer depends on `click` (it ships its own command layer) and
  `typing-extensions` is not needed on Python 3.11+, so the real tree is the one
  listed above. `uv.lock` records every resolved version.
- **Rationale**: Typer provides typed commands, generated help, and a testable runner in
  one dependency, which is the smallest surface that satisfies "a console tool" without
  hand-rolling argument parsing. `sqlite3` is already in the standard library, so no
  database driver is needed. The standard library is preferred over every third-party
  option per Principle IV.
- **Alternatives considered**: (a) `argparse` only — rejected, it duplicates what Typer
  provides with far more boilerplate and weaker test ergonomics; (b) `click` directly —
  rejected, Typer is the layer the user asked for and already includes what it needs;
  (c) SQLAlchemy — rejected, an ORM is disproportionate for three tables and adds a
  major dependency; (d) Alembic — rejected, a single additive schema does not need a
  migration framework.

### R15 — Toolchain bootstrap

- **Decision**: Python 3.11+ is the minimum supported version. The project is packaged
  with `pyproject.toml` (PEP 621) using a `src/` layout and an entry point
  `devlog = "devlog.cli:app"`. Because the local interpreter ships without a `pip`
  module, the documented bootstrap uses `uv` (already present on the machine) with
  `uv venv` and `uv pip install -e ".[dev]"`; `python -m venv` plus `ensurepip` is the
  documented fallback. The test suite runs with `pytest` inside that environment.
- **Rationale**: The quickstart has to be runnable on the actual machine, so the bootstrap
  path must match what is installed. `uv` needs no new tooling and creates an isolated
  environment, which also keeps the developer's system interpreter clean.
- **Alternatives considered**: (a) requiring a globally installed `pip` — rejected, the
  system interpreter has none; (b) committing the virtual environment — rejected, it
  pollutes the repository; (c) `pipx` for a user-level install — rejected, it is for
  publishing finished tools, and adds an installation layer the project does not need.

## Spec Sync Required — applied on 2026-10-21

The following edits have been applied to `spec.md` (and the checklist item "No
[NEEDS CLARIFICATION] markers remain" re-validated and now passes). The clarifications
are also recorded in the spec's `## Clarifications` section:

| Spec location | Change |
|---|---|
| FR-003 | Replace the marker with the resolved rule: single store at `~/.devlog/notes.db`, overridable via `DEVLOG_DB_PATH`, created additively, never deleted or reset automatically. |
| FR-010 | Replace the marker with the resolved rule: exact matching on the normalised tag, AND semantics across multiple tags. |
| FR-012 | Replace the marker with the resolved rule: v1 covers create, list, search by tags, and export; editing and deleting are out of scope for v1. |
| FR-014 | Add that the default export destination is `./devlog-notes.md` and that `--force` counts as explicit confirmation at that moment. |
| FR-021 | Add the concrete exit-code contract (0 success, 1 operational error, 2 usage/validation error, 3 no results). |
| FR-008 | Add that the listing is rendered as plain text, one note per line, newest first. |
| Assumptions → Local storage | Replace "the specific path of the file is pending confirmation (see FR-003)" with the confirmed path. |
| Assumptions → Search scope | Replace "exact vs. partial match details and combining multiple tags are pending confirmation (see FR-010)" with the confirmed semantics. |

## Open Questions Deferred to Implementation

None that block planning. The following remain implementation-level choices, explicitly
out of scope for clarification: module and function naming, the exact SQL text, the
internal exception class names, and the wording of individual Spanish strings that are
not contractually fixed.

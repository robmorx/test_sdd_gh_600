# Feature Specification: DevLog CLI

**Feature Branch**: `001-devlog-cli`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "I want to build DevLog CLI, a console tool to save development notes in SQLite. It allows creating, listing, searching by tags, and exporting notes to Markdown. It does not need authentication or a complex graphical interface."

## Clarifications

### Session 2026-10-21

- Q: Where on the user's machine should the tool keep the SQLite database file that holds the notes? (FR-003) → A: Option A — one single fixed file under the user's home directory (`~/.devlog/notes.db`), the same store no matter which folder the command runs from; the path can be overridden with the `DEVLOG_DB_PATH` environment variable for isolated use and for the test suite.
- Q: Should tag matching be exact or support partial substring matches, and must a result contain all requested tags or is any of them enough? (FR-010) → A: Exact matching against the normalised tag value, with AND semantics — a note is returned only when it carries every requested tag. Partial matching and OR-matching are out of scope for v1. (Decided during planning — `research.md` R2.)
- Q: Is the scope limited to the four capabilities indicated in the input, or does it also include editing and deleting already created notes? (FR-012) → A: v1 is limited to create, list, search by tags, and export; editing and deleting notes are out of scope and require an explicit scope expansion. (Decided during planning — `research.md` R3.)
- Q: What exit codes must the tool use to distinguish success, absence of results, and error? (FR-021) → A: `0` success, `1` operational error, `2` usage or validation error, `3` no results. (`research.md` R5.)
- Q: Where is the exported Markdown file written when the user does not choose a path? (FR-014) → A: The default destination is `./devlog-notes.md` in the current directory; `--output/-o` selects another path. (`research.md` R4.)
- Q: In what format is the note listing rendered? (FR-008) → A: One note per line as `#<id>  <date>  <tags>  <title>`, newest first, plain text with no table or pagination. (`research.md` R13.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save a development note (Priority: P1)

As a developer who just solved a problem or saved a useful command, I want to record that note from the terminal with a title, optional text, and tags, and be certain that it is permanently saved so that I do not lose that knowledge.

**Why this priority**: Without note capture, there is no product; all other capabilities (listing, searching, exporting) depend on having saved notes.

**Independent Test**: Can be tested independently by running the creation of a note with a title, content, and tags, and then verifying that the note appears in the general listing; it provides value on its own as a notebook.

**Acceptance Scenarios**:

1. **Given** a fresh installation with no database, **When** the user creates a note with the title "CORS error in staging", descriptive content, and the tags `bug` and `api`, **Then** the note is saved and a confirmation message is displayed with its creation date.
2. **Given** the user is in the terminal, **When** they create a note providing only a title, **Then** the note is saved correctly and the content and tags remain empty.
3. **Given** a saved note, **When** the user closes the terminal and reopens it later, **Then** the note remains available and appears in the listing.

---

### User Story 2 - View my notes (Priority: P2)

As a developer with hundreds of accumulated notes, I want to see a list of all my notes with their title, date, and tags, to quickly orient myself on what I have saved without opening files one by one.

**Why this priority**: Once notes accumulate, retrieving them is the next primary value; it is the capability that makes the notebook useful on a daily basis.

**Independent Test**: Can be tested independently by creating multiple notes with different dates and verifying that the listing returns all of them, ordered from newest to oldest with visible title, date, and tags.

**Acceptance Scenarios**:

1. **Given** three saved notes with different dates, **When** the user requests the listing, **Then** all three appear with their title, creation date, and tags, ordered from newest to oldest.
2. **Given** a user who does not have any notes yet, **When** they request the listing, **Then** the tool informs them that there are no saved notes and does not display an error.
3. **Given** a saved note without tags, **When** the user requests the listing, **Then** that note still appears, showing that it has no tags.

---

### User Story 3 - Search notes by tag (Priority: P3)

As a developer who remembers solving an authentication problem but not the exact date or content, I want to filter my notes by one or more tags to retrieve relevant notes in seconds.

**Why this priority**: Search turns the notebook into a reference tool and is the main time-saver compared to reading the complete listing.

**Independent Test**: Can be tested independently by creating notes with different tag combinations and verifying that the search returns exactly the notes matching the requested tag and no others.

**Acceptance Scenarios**:

1. **Given** notes with the tags `bug`, `api`, and `idea`, **When** the user searches for `bug`, **Then** only notes having that tag are returned.
2. **Given** a tag that does not exist in any note, **When** the user searches for it, **Then** the tool informs that there are no matches and returns no results.
3. **Given** a search result, **When** it is displayed, **Then** each returned note includes its title, date, and tags for identification.

---

### User Story 4 - Export my notes to Markdown (Priority: P4)

As a developer who wants to share their knowledge base with the team or archive it, I want to export all my notes to a readable Markdown file to review, version, or publish them outside the tool.

**Why this priority**: Exporting is the way to extract the notebook's value outside the tool; it is valuable but not necessary for daily use inside the terminal.

**Independent Test**: Can be tested independently by exporting a known set of notes and verifying that the generated Markdown file contains each note with its title, date, tags, and content without losing information.

**Acceptance Scenarios**:

1. **Given** saved notes, **When** the user requests export, **Then** a Markdown file is generated containing all notes with title, creation date, tags, and content.
2. **Given** a pre-existing Markdown file at the destination path, **When** the user attempts to export, **Then** the tool asks for explicit confirmation before replacing it.
3. **Given** notes with content including line breaks, lists, or special characters, **When** exported, **Then** the Markdown file preserves that content readably and uncorrupted.

---

### Edge Cases

- What happens on first use, when the data store does not exist yet? The tool creates it automatically without prompting and without touching any prior data.
- What happens if the database file exists but is corrupted or unreadable? The tool displays a clear error, explains what to do, and does not automatically delete, recreate, or reset the file.
- What happens if the user enters an empty title or one consisting only of spaces? The tool rejects the note with an understandable validation message and saves nothing.
- What happens if the user repeats the same tag or writes it with different capitalization? The tag is normalized (trimmed and lowercase) and is not stored duplicated within the same note.
- What happens if the user searches for a tag that does not exist? It informs that there are no matches, with an exit code indicating it was not a technical error.
- What happens if the search returns no results and the user also requests the normal listing? Both operations are independent and work separately.
- What happens if the user exports when they have no notes? The tool generates an empty but valid Markdown file and informs that there were no notes to export.
- What happens if the user specifies an export path in a non-existent directory or without write permissions? The tool displays a clear error and leaves no partial files.
- What happens if a note's content contains quotes, line breaks, or Markdown characters? The content is preserved intact and rendered safely in the export.
- What happens if two concurrent operations attempt to write at the same time? The tool completes one operation and the other receives a clear message, without data corruption.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow the user to create a note with a mandatory title, optional content, and zero or more tags.
- **FR-002**: The system MUST assign each note a unique identifier, its creation date and time, and MUST preserve them throughout the life of the note.
- **FR-003**: The system MUST persist notes in a single local SQLite store located at `~/.devlog/notes.db` under the user's home directory, MUST allow that path to be overridden through the `DEVLOG_DB_PATH` environment variable, and MUST create the store and its schema automatically and additively on first use, without ever deleting, resetting, or recreating an existing store.
- **FR-004**: The system MUST preserve note data between executions: closing the tool or restarting the computer must not alter saved notes.
- **FR-005**: The system MUST list the notes saved by the user.
- **FR-006**: The listing MUST display, at a minimum, the title, creation date, and tags of each note.
- **FR-007**: The listing MUST order notes from newest to oldest.
- **FR-008**: The listing MUST run without requiring any filter, MUST explicitly indicate when no saved notes exist, and MUST render one note per line as `#<id>  <date>  <tags>  <title>`, ordered from newest to oldest.
- **FR-009**: The system MUST search for notes based on one or more tags specified by the user.
- **FR-010**: The search scope MUST match tags exactly against the normalised tag value (trimmed and lowercased), and when several tags are specified the result MUST require the note to carry every one of them (AND). Partial substring matching and OR-matching are out of scope for v1.
- **FR-011**: The search result MUST display the title, date, and tags of each matching note and MUST clearly distinguish the case with no matches.
- **FR-012**: The system MUST export saved notes to a Markdown file. The scope of existing note management is limited to the four capabilities indicated in the input (create, list, search by tags, and export); editing and deleting already created notes are out of scope for v1 and require an explicit scope expansion.
- **FR-013**: The export MUST include, for each note, its title, creation date, tags, and content in a readable Markdown format.
- **FR-014**: The export MUST offer the user the ability to choose the destination file path (defaulting to `./devlog-notes.md` in the current directory) and MUST report the operation result.
- **FR-015**: The system MUST NOT overwrite an existing export file without explicit user confirmation at that moment; an explicit `--force` flag counts as that confirmation, and in a non-interactive session without it the tool MUST refuse and leave the existing file untouched.
- **FR-016**: The system MUST validate that a note title is not empty and does not consist solely of spaces, and MUST report the error without saving anything.
- **FR-017**: The system MUST normalize tags (trim spaces and unify case) and MUST NOT store the same tag twice within the same note.
- **FR-018**: The system MUST preserve note content intact, including line breaks and special characters, and MUST render it safely in the export.
- **FR-019**: The system MUST NOT perform destructive operations on the data store (deletion, reset, or schema recreation) automatically or implicitly: any such operation requires explicit user approval at that moment.
- **FR-020**: The system MUST display understandable error messages, without technical traces, indicating what failed and what action the user must take.
- **FR-021**: The system MUST communicate the result of each operation via an exit code distinguishing between successful execution (`0`), absence of results (`3`), and error (`1` for operational failures, `2` for usage and validation failures).
- **FR-022**: The system MUST NOT require authentication, user accounts, or credentials of any kind, and MUST run entirely in the terminal without a graphical interface.
- **FR-023**: The system MUST run completely locally, without depending on remote services or network connection.
- **FR-024**: Each tool capability (create, list, search, and export) MUST have automated tests covering both the success path and error paths, and the tests MUST NOT depend on external services or the network.
- **FR-025**: The system MUST NOT incorporate third-party dependencies that have not been justified and pre-approved.

### Key Entities

- **Note**: The central record of the product. It is uniquely identified and contains a title (mandatory), text content (optional), a creation date and time, and its tags. It is the unit that the user creates, lists, searches, and exports.
- **Tag**: The user classification mechanism. It is a short text normalized before saving and associated with one or more notes. Multiple notes can share the same tag, and a note may have none.
- **Export Result**: The Markdown file generated from a set of notes. It is a derived result, not a stored record; it does not become part of the notes again.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user who has just installed the tool can create their first complete note (title, content, and tags) in less than 1 minute from the terminal.
- **SC-002**: A user without documentation can complete the workflow create -> list -> search by tag in less than 5 minutes without external help.
- **SC-003**: 100% of existing notes appear in the listing, without omissions or duplicates, verified over a set of 500 notes.
- **SC-004**: Listing 500 notes completes in less than 3 seconds on a reference desktop computer.
- **SC-005**: 100% of notes returned by a search meet the tag matching condition, verified over a set of notes with overlapping tag combinations.
- **SC-006**: Exporting 500 notes produces a Markdown file containing 100% of the notes, with title, date, tags, and content, and without character corruption.
- **SC-007**: The tool executes 0 destructive operations on the data store during normal operation, verified over the complete trace of user actions.
- **SC-008**: 100% of tool capabilities (create, list, search, and export) have automated tests that pass repeatedly and without network access.
- **SC-009**: 95% of executions end without unexplained errors; all displayed errors indicate the cause and corrective action in understandable language.
- **SC-010**: The tool is usable from start to finish by a single person in their local terminal, without accounts, without a server, and without a network connection.

## Assumptions

- **Single local actor**: The tool is used by a single person on their own machine; there are no simultaneous users or need to share the same note store between people.
- **Local storage**: The input description indicates SQLite as the storage engine; it is kept as a product restriction. The store is a single file at `~/.devlog/notes.db`, and the path can be overridden with the `DEVLOG_DB_PATH` environment variable (see FR-003).
- **No authentication**: By explicit indication from the input, there will be no accounts, passwords, sessions, or any identity mechanism.
- **Terminal-only interface**: There will be no graphical interface, web dashboard, desktop integration, or editor integration, as indicated in the input.
- **Out-of-scope functionality for v1**: Editing and deleting existing notes, free-text search within content, additional categories (e.g., `bug`, `command`, `idea`), attaching files or images, cloud synchronization, export formats other than Markdown, and any form of automatic sharing or publishing. Their incorporation will require an explicit scope expansion (Constitution Principle V).
- **Search scope**: Search is defined around tags, with exact matching against the normalised tag and AND semantics when several tags are given (see FR-010).
- **Tags**: A model of free tags without hierarchies or colors is assumed, without a predefined vocabulary restricting what the user can write.
- **Date format**: Dates are displayed to the user in a readable local format with year, month, day, hour, and minutes.
- **Interface language**: The tool communicates with the user in Spanish, consistent with the project's working language.
- **No network**: It will not talk to remote services; the tool operates offline.
- **Fault integrity**: In the event of a storage error, the tool never deletes or rebuilds the data file on its own; it reports the issue and leaves data intact (Constitution Principle II).
# AnkiTransform v2 — Spanish Pipeline Design

**Date:** 2026-06-20
**Status:** Approved (pending spec review)
**Author:** brainstormed with Claude Code

## Summary

Rework the AnkiTransform repo into two clearly separated parts and migrate the
Spanish flashcard workflow off the GitHub Copilot agent and onto Claude Code +
the [anki-mcp-server](https://github.com/ankimcp/anki-mcp-server) (which talks to
Anki live via the AnkiConnect add-on).

The new Spanish workflow: **drop textbook photos in a folder → tell Claude to run
it → Claude reads the photos with vision, authors well-designed cards, checks for
duplicates against the live deck, and pushes them straight into Anki.** No more
Tesseract OCR, no more manual `.apkg` import.

Part 1 (PDF → PNG) is intentionally left functionally untouched — only relocated.

## Goals

- One low-friction trigger to turn new photos into live Anki cards.
- **No duplicate cards** — checked against the real collection, not a local file.
- **Better-looking, better-for-learning cards** for both vocab and grammar.
- Smarter study method than plain ES↔DE pairs.
- Reuse existing code/styling where it still serves the goal.

## Non-Goals

- Reworking the PDF → PNG converter (only move it).
- Building a GUI. The trigger is Claude Code (slash command or plain text).
- Offline `.apkg` export as the primary path (kept only as an optional fallback).

## Decisions (locked in during brainstorming)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Vocab card types | **Recognition (ES→DE) + Production (DE→ES) + Cloze** (3 cards/word). Example sentences are AI-generated. |
| 2 | Grammar card types | **Smart hybrid**: conjugation/declension tables → cloze (one card per row); reference content (alphabet, pronunciation, rule lists) → reference card. Full table always available on the back. |
| 3 | Card delivery | **Direct into the live deck** via MCP `addNotes`. Claude does all the work; no per-batch approval gate. A summary report is printed after each run. |
| 4 | Trigger | Claude drives end-to-end. Invoked via a `/spanish` command **or** plain-language ("new cards in the folder, run it"). Procedure captured in a project skill so both paths behave identically. |
| 5 | Existing 439 cards | **Keep as-is** (preserve Anki review history). Provide a separate, **non-destructive** one-time upgrade (adds new-format cards, suspends old ones — never deletes) the user can run later at their discretion. |
| 6 | OCR | **Dropped.** Claude reads photos directly with vision (vocab columns and grammar tables). Removes the Tesseract/rotation/thumbnail/`recognition_issues` machinery. |
| 7 | Deduplication | Via live `findNotes` query before adding. Replaces the local `dedup_cards.py`. |

## Architecture

### Repo layout

```
AnkiTransform/
├── pdf-to-png/              # Part 1 — relocated, unchanged
│   ├── convert.py
│   └── README.md
├── spanish/                 # Part 2 — the rework
│   ├── inbox/               # user drops new photos here
│   ├── archive/             # processed photos moved here after a run
│   ├── models/              # the 3 note-type definitions (fields/templates/CSS) — source of truth
│   │   ├── vocab.py         # ES Vocab model spec
│   │   ├── cloze.py         # ES Cloze model spec
│   │   ├── grammar.py       # ES Grammar model spec
│   │   └── styles.css       # shared card CSS (lifted from old build_deck.py)
│   ├── cards.json           # running audit log of everything authored (offline backup)
│   ├── upgrade_legacy.md    # the optional non-destructive upgrade procedure
│   └── README.md
├── docs/superpowers/specs/  # this spec
├── .claude/
│   └── skills/spanish/      # the documented pipeline procedure (runnable as /spanish)
│       └── SKILL.md
└── .mcp.json                # anki-mcp-server registration
```

### Pipeline flow

1. User drops photos in `spanish/inbox/`.
2. User triggers Claude (`/spanish` or plain text).
3. Claude **reads each photo with vision** — extracts vocab pairs and grammar tables.
4. Claude **authors cards**:
   - Vocab → Recognition + Production notes, plus a Cloze note built from an
     AI-generated example sentence (Spanish sentence + German gloss; the target
     word is the cloze deletion).
   - Grammar → cloze rows for conjugation/declension; reference card otherwise.
5. Claude **dedups** with `findNotes` against the live deck (normalized match on
   the Spanish term / sentence) and drops anything already present.
6. Claude **pushes** the survivors via `addNotes` (batched, ≤100 per call).
7. Claude **archives** the photos to `spanish/archive/` and appends authored
   cards to `cards.json`.
8. Claude prints a **report**: counts added per type, duplicates skipped, and any
   words it was unsure about (asking the user rather than guessing).

### Note types (created in Anki once via MCP `createModel`)

**ES Vocab** — fields: `Spanish`, `Grammar` (gender/POS tag), `German`,
`Example_ES`, `Example_DE`, `Notes`, `Source`.
Templates: `ES → DE` (Recognition) and `DE → ES` (Production). CSS from existing
`build_deck.py`.

**ES Cloze** — Anki's built-in cloze type, styled to match. Fields: `Text`
(sentence with `{{c1::word}}`), `Translation` (German gloss), `Notes`, `Source`.

**ES Grammar** — fields: `Title`, `Table_HTML`, `Notes`, `Source`. Reference
tables use a title→table template. Conjugation/declension tables are emitted
instead as ES Cloze notes (one per row), with the full table retained in the
extra/`Notes` field for context.

### Card content principles

- **Faithful extraction** for vocab/grammar terms — never invent vocabulary.
- **Example sentences are explicitly allowed to be generated** (this is the one
  deliberate departure from the old "never invent content" rule). They must be
  simple, level-appropriate, use the target word naturally, and come with a
  German gloss. When unsure, Claude asks rather than fabricates.

## Deduplication

Before adding any note, query the live collection:
`findNotes` with a deck-scoped query on the normalized Spanish field (strip
Lektion prefix, NFC-normalize, lowercase, collapse whitespace — same normalization
the old `dedup_cards.py` used). Cloze notes dedup on the sentence text. Skip exact
matches; report the count.

## Setup / prerequisites

1. Install **AnkiConnect** add-on in Anki (code `2055492159`). Anki must be
   running for any push.
2. Register `anki-mcp-server` in `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "anki-mcp": {
         "command": "npx",
         "args": ["-y", "@ankimcp/anki-mcp-server", "--stdio"],
         "env": { "ANKI_CONNECT_URL": "http://localhost:8765" }
       }
     }
   }
   ```
3. Verify connection (`listDecks`), then **inspect the current live Spanish deck**
   to confirm the existing field layout and look for quality improvements before
   finalizing model creation.

## What gets removed

- `src/spanishExtract/ocr_extract.py` (Tesseract OCR).
- `src/spanishExtract/dedup_cards.py` (replaced by live `findNotes`).
- `.github/agents/flashcard.agent.md` (Copilot agent).
- The `ocr` / `dedup` / `build` subcommands in `main.py`.
- genanki `.apkg` build as the primary path (CSS/templates are salvaged into the
  new model specs; an optional offline export may be kept as a fallback).

## Risks / open questions

- **Anki must be open** for pushes. The pipeline should fail clearly with a
  "start Anki + AnkiConnect" message if `listDecks` is unreachable.
- **Example-sentence quality** — generated sentences need to stay simple and
  correct. Mitigation: keep them short, gloss in German, surface low-confidence
  ones in the report.
- **Review-load** — 3 cards/word grows the daily queue quickly. Acceptable to the
  user; revisit if it becomes overwhelming (could disable the Recognition card).
- **Legacy upgrade** is deferred and optional; its detailed procedure lives in
  `spanish/upgrade_legacy.md` and is out of scope for the first implementation.

## Success criteria

- Dropping new photos + one trigger results in correctly-styled cards appearing
  in the live Anki deck with zero duplicates.
- Vocab produces Recognition + Production + Cloze; grammar follows the hybrid rule.
- No Tesseract, no manual `.apkg` import in the happy path.
- Existing review history untouched.

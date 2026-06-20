# Spanish — photo → Anki pipeline

Drop textbook photos in `inbox/`, then tell Claude **"run the Spanish pipeline"** (or `/spanish`).
Claude reads the photos, authors cards, removes duplicates against your live deck, and pushes
them into Anki via the `anki-mcp` server. No manual `.apkg` import.

## Card design
- **Vocab** → 3 cards/word: Recognition (ES→DE), Production (DE→ES), and a Cloze example sentence.
- **Grammar** → conjugation/declension tables become cloze (one card per row); reference tables
  (alphabet, pronunciation, rules) become a single reference card.

## Prerequisites
- Anki desktop **running** with the **AnkiConnect** add-on (code `2055492159`).
- The `anki-mcp` MCP server registered (see `../.mcp.json`).
- Note types created once: `uv run python -m spanish.models` → create each via MCP `createModel`.

## Layout
- `inbox/` — drop new photos here (photos are local-only, not tracked in git).
- `archive/` — processed photos land here automatically (also git-ignored).
- `models/` — note-type definitions (fields, templates, CSS) = source of truth.
- `cards.json` — running audit log of authored cards.
- `build_notes.py` / `normalize.py` — deterministic, tested transform + dedup helpers.

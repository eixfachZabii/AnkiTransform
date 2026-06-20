# Spanish Anki Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework AnkiTransform into two top-level parts and replace the Copilot/OCR/`.apkg` Spanish workflow with a vision-first, MCP-driven pipeline that pushes well-designed cards straight into the live Anki deck.

**Architecture:** Claude reads textbook photos with vision and authors entries into `spanish/cards.json`. A deterministic, tested Python module (`spanish/build_notes.py`) turns those entries into AnkiConnect note payloads (Recognition + Production + Cloze for vocab; cloze-per-row or reference for grammar). Card note types are defined once in Python (`spanish/models/`) as the single source of truth and created in Anki via the anki-mcp-server `createModel` tool. Claude orchestrates dedup (`findNotes`) and insertion (`addNotes`) through the MCP server, following a documented `/spanish` skill.

**Tech Stack:** Python ≥3.10, uv (deps), pytest (tests), anki-mcp-server + AnkiConnect (Anki integration), Claude vision (photo reading).

## Global Constraints

- Python `>=3.10`; manage all dependencies with **uv** (never pip directly).
- Tests run with `uv run pytest` from the repo root.
- All writes to Anki go **through the anki-mcp-server MCP tools** — never bypass with direct HTTP to AnkiConnect from Python.
- Vocab/grammar **terms are extracted faithfully** from photos and never invented. **Example sentences ARE allowed to be AI-generated** (simple, level-appropriate, German-glossed).
- Existing cards are **never deleted**; the legacy deck is preserved untouched (the optional upgrade is out of scope here).
- Exact model names (used verbatim everywhere): `AnkiTransform ES Vocab`, `AnkiTransform ES Cloze`, `AnkiTransform ES Grammar`.
- Default target deck name comes from `spanish/cards.json` → `deck_name` (`AnkiTransform::ES→DE::Lektion 0-1`).

---

### Task 1: Restructure repo, prune old code, set up tooling

**Files:**
- Create: `pdf-to-png/convert.py` (moved from `src/pdfExtract/convert.py`, + CLI)
- Create: `pdf-to-png/README.md`
- Create: `spanish/__init__.py`, `spanish/inbox/.gitkeep`, `spanish/archive/.gitkeep`
- Create: `spanish/cards.json`, `spanish/cards.legacy.json` (moved data)
- Create: `tests/__init__.py`
- Modify: `pyproject.toml`
- Delete: `src/` (whole tree), `main.py`, `.github/agents/flashcard.agent.md`, `input/` OCR artifacts

**Interfaces:**
- Produces: `pdf-to-png/convert.py` with `batch_convert(input_folder, output_folder, dpi)`; a Python-importable `spanish` package; `spanish/cards.json` schema `{deck_name, lang_front, lang_back, cards: []}`.

- [ ] **Step 1: Create the new folder skeleton**

```bash
mkdir -p pdf-to-png spanish/inbox spanish/archive spanish/models tests
touch spanish/inbox/.gitkeep spanish/archive/.gitkeep
printf '' > spanish/__init__.py
printf '' > tests/__init__.py
```

- [ ] **Step 2: Move the PDF converter and give it a CLI**

```bash
git mv src/pdfExtract/convert.py pdf-to-png/convert.py
```

Append this to the end of `pdf-to-png/convert.py`:

```python


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert all PDFs in a folder to PNG images"
    )
    parser.add_argument("--input-dir", default="input")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    batch_convert(args.input_dir, args.output_dir, args.dpi)
```

- [ ] **Step 3: Preserve the legacy cards data, start a fresh cards.json**

```bash
git mv src/spanishExtract/cards.json spanish/cards.legacy.json 2>/dev/null || mv src/spanishExtract/cards.json spanish/cards.legacy.json
```

Create `spanish/cards.json`:

```json
{
  "deck_name": "AnkiTransform::ES→DE::Lektion 0-1",
  "lang_front": "es",
  "lang_back": "de",
  "cards": []
}
```

- [ ] **Step 4: Archive the already-processed photos, drop OCR artifacts**

```bash
# keep the original photos as processed history
mv input/IMG_*.jpeg spanish/archive/ 2>/dev/null || true
# remove now-obsolete OCR outputs (thumbnails, per-image text, combined text)
rm -f spanish/archive/*.thumb.jpeg input/*.txt input/all_ocr.txt
rmdir input 2>/dev/null || true
```

- [ ] **Step 5: Delete the obsolete code**

```bash
rm -rf src
rm -f main.py
rm -f .github/agents/flashcard.agent.md
rmdir .github/agents .github 2>/dev/null || true
```

- [ ] **Step 6: Write `pdf-to-png/README.md`**

```markdown
# PDF → PNG

Converts PDF slide decks into per-page PNGs for Anki. Unchanged from v1, just relocated.

## Usage

```bash
uv run python pdf-to-png/convert.py --input-dir input --output-dir output --dpi 300
```

Each PDF becomes a subfolder of `--output-dir` containing `page_001.png`, `page_002.png`, …
```

- [ ] **Step 7: Update `pyproject.toml`**

Replace the whole file with:

```toml
[project]
name = "ankitransform"
version = "0.2.0"
description = "Turn textbook photos into Anki flashcard decks"
requires-python = ">=3.10"
dependencies = [
    "pdf2image",
    "pillow",
]

[dependency-groups]
dev = [
    "pytest>=8",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

(Note: `genanki` and `pytesseract` are intentionally dropped — no OCR, no `.apkg` build. The `[project.scripts]` entry is removed because `main.py` is gone.)

- [ ] **Step 8: Sync the environment**

Run: `uv sync`
Expected: resolves without `genanki`/`pytesseract`, installs `pytest` in the dev group.

- [ ] **Step 9: Verify the restructure**

Run: `uv run python pdf-to-png/convert.py --help`
Expected: argparse help text for `--input-dir/--output-dir/--dpi`, no import errors.

Run: `uv run python -c "import spanish; print('ok')"`
Expected: `ok`

Run: `uv run pytest -q`
Expected: `no tests ran` (exit code 5 is fine — collection works, just nothing to run yet).

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "refactor: split repo into pdf-to-png/ and spanish/, drop OCR/genanki/Copilot agent"
```

---

### Task 2: `normalize()` — dedup key normalization

**Files:**
- Create: `spanish/normalize.py`
- Test: `tests/test_normalize.py`

**Interfaces:**
- Produces: `normalize(text: str) -> str` — strips a leading `"<n>. "` Lektion prefix, NFC-normalizes, lowercases, strips, and collapses internal whitespace. Used by `build_notes.py` (Task 4) to compute `dedup_key`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_normalize.py`:

```python
from spanish.normalize import normalize


def test_strips_lektion_prefix():
    assert normalize("1. la tarde") == "la tarde"
    assert normalize("0. ¿Cómo te llamas?") == "¿cómo te llamas?"


def test_lowercases_and_collapses_whitespace():
    assert normalize("  La   Tarde ") == "la tarde"


def test_nfc_equivalence():
    # combining tilde vs precomposed ñ must normalize equal
    assert normalize("español") == normalize("español")


def test_no_prefix_left_untouched():
    assert normalize("el coche") == "el coche"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_normalize.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'spanish.normalize'`

- [ ] **Step 3: Write minimal implementation**

Create `spanish/normalize.py`:

```python
"""Text normalization for duplicate detection."""
import re
import unicodedata

_PREFIX_RE = re.compile(r"^\d+\.\s*")
_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Normalize for comparison: strip Lektion prefix, NFC, lowercase, collapse whitespace."""
    text = _PREFIX_RE.sub("", text)
    text = unicodedata.normalize("NFC", text)
    text = text.lower().strip()
    text = _WS_RE.sub(" ", text)
    return text
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_normalize.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add spanish/normalize.py tests/test_normalize.py
git commit -m "feat(spanish): normalize() for dedup keys"
```

---

### Task 3: Card model specs (single source of truth)

**Files:**
- Create: `spanish/models/styles.py`
- Create: `spanish/models/vocab.py`
- Create: `spanish/models/cloze.py`
- Create: `spanish/models/grammar.py`
- Create: `spanish/models/__init__.py`
- Create: `spanish/models/__main__.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces:
  - `spanish.models.styles.CARD_CSS: str` — shared card CSS.
  - `spanish.models.vocab.spec() -> dict`, `cloze.spec() -> dict`, `grammar.spec() -> dict` — each returns an AnkiConnect `createModel` param dict with keys `modelName, inOrderFields, isCloze, css, cardTemplates`.
  - `spanish.models.ALL_MODELS: list[dict]` — `[vocab.spec(), cloze.spec(), grammar.spec()]`.
  - `python -m spanish.models` prints `json.dumps(ALL_MODELS)` to stdout (Claude feeds each entry to the MCP `createModel` tool in Task 5).

- [ ] **Step 1: Write the failing test**

Create `tests/test_models.py`:

```python
import json
import subprocess
import sys

from spanish.models import ALL_MODELS
from spanish.models import vocab, cloze, grammar


def test_vocab_spec():
    s = vocab.spec()
    assert s["modelName"] == "AnkiTransform ES Vocab"
    assert s["inOrderFields"] == [
        "Spanish", "Grammar", "German", "Example_ES", "Example_DE", "Notes", "Source",
    ]
    assert s["isCloze"] is False
    assert len(s["cardTemplates"]) == 2
    assert s["cardTemplates"][0]["Name"] == "ES → DE"
    assert s["cardTemplates"][1]["Name"] == "DE → ES"
    assert s["css"].strip()


def test_cloze_spec_is_cloze():
    s = cloze.spec()
    assert s["modelName"] == "AnkiTransform ES Cloze"
    assert s["isCloze"] is True
    assert s["inOrderFields"] == ["Text", "Translation", "Notes", "Source"]
    assert "{{cloze:Text}}" in s["cardTemplates"][0]["Front"]


def test_grammar_spec():
    s = grammar.spec()
    assert s["modelName"] == "AnkiTransform ES Grammar"
    assert s["inOrderFields"] == ["Title", "Table_HTML", "Notes", "Source"]
    assert s["isCloze"] is False
    assert "{{Table_HTML}}" in s["cardTemplates"][0]["Back"]


def test_all_models_three_unique_names():
    names = [m["modelName"] for m in ALL_MODELS]
    assert len(names) == 3
    assert len(set(names)) == 3


def test_module_main_prints_valid_json():
    out = subprocess.check_output(
        [sys.executable, "-m", "spanish.models"], cwd="."
    )
    parsed = json.loads(out)
    assert [m["modelName"] for m in parsed] == [
        "AnkiTransform ES Vocab",
        "AnkiTransform ES Cloze",
        "AnkiTransform ES Grammar",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'spanish.models'`

- [ ] **Step 3: Write the shared CSS**

Create `spanish/models/styles.py` (CSS salvaged from the old `build_deck.py`, extended for examples + cloze):

```python
"""Shared card CSS — single source of truth for all AnkiTransform ES note types."""

CARD_CSS = """
.card {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 24px;
    text-align: center;
    color: #1a1a2e;
    background: #f8f9fa;
    padding: 20px;
}
.direction {
    font-size: 12px; font-weight: 700; color: #999;
    text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;
}
.word { font-size: 32px; font-weight: 600; margin: 20px 0; color: #16213e; }
.grammar {
    display: inline-block; background: #e63946; color: white;
    font-size: 13px; font-weight: 700; padding: 3px 10px; border-radius: 12px;
    margin-bottom: 12px; letter-spacing: 0.5px; text-transform: lowercase;
}
.translation { font-size: 28px; font-weight: 500; color: #0f3460; margin: 16px 0; }
.example {
    font-size: 18px; color: #16213e; margin: 14px auto; max-width: 90%;
    padding: 10px 14px; background: #eef1f5; border-radius: 8px;
}
.example-de { font-size: 15px; color: #66707a; font-style: italic; }
.notes {
    font-size: 15px; color: #666; font-style: italic; margin-top: 10px;
    padding: 8px 16px; background: #e9ecef; border-radius: 8px; display: inline-block;
}
.source { font-size: 11px; color: #aaa; margin-top: 20px; }
hr#answer { border: none; border-top: 1px solid #dee2e6; margin: 20px 0; }
.cloze-sentence { font-size: 24px; color: #16213e; margin: 18px 0; }
.cloze { font-weight: 800; color: #e63946; }

/* Grammar tables */
table { border-collapse: collapse; margin: 16px auto; font-size: 18px; min-width: 300px; }
table th { background: #16213e; color: white; padding: 8px 14px; font-weight: 600; text-align: center; }
table td { border: 1px solid #dee2e6; padding: 7px 14px; text-align: center; color: #1a1a2e; }
table tr:nth-child(even) td { background: #e9ecef; }
table td b { color: #16213e; }
""".strip()
```

- [ ] **Step 4: Write the vocab model spec**

Create `spanish/models/vocab.py`:

```python
"""ES Vocab note type — Recognition (ES→DE) + Production (DE→ES) cards."""
from spanish.models.styles import CARD_CSS

MODEL_NAME = "AnkiTransform ES Vocab"

_EXAMPLE_BLOCK = (
    '{{#Example_ES}}<div class="example">{{Example_ES}}'
    '<br><span class="example-de">{{Example_DE}}</span></div>{{/Example_ES}}'
)
_NOTES_BLOCK = '{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}'
_SOURCE_BLOCK = '{{#Source}}<div class="source">📷 {{Source}}</div>{{/Source}}'


def spec() -> dict:
    return {
        "modelName": MODEL_NAME,
        "inOrderFields": [
            "Spanish", "Grammar", "German", "Example_ES", "Example_DE", "Notes", "Source",
        ],
        "isCloze": False,
        "css": CARD_CSS,
        "cardTemplates": [
            {
                "Name": "ES → DE",
                "Front": (
                    '<div class="direction">ES → DE</div>\n'
                    '<div class="word">{{Spanish}}</div>\n'
                    '{{#Grammar}}<div class="grammar">{{Grammar}}</div>{{/Grammar}}'
                ),
                "Back": (
                    '{{FrontSide}}\n<hr id="answer">\n'
                    '<div class="translation">{{German}}</div>\n'
                    f"{_EXAMPLE_BLOCK}\n{_NOTES_BLOCK}\n{_SOURCE_BLOCK}"
                ),
            },
            {
                "Name": "DE → ES",
                "Front": (
                    '<div class="direction">DE → ES</div>\n'
                    '<div class="word">{{German}}</div>'
                ),
                "Back": (
                    '{{FrontSide}}\n<hr id="answer">\n'
                    '<div class="translation">{{Spanish}}</div>\n'
                    '{{#Grammar}}<div class="grammar">{{Grammar}}</div>{{/Grammar}}\n'
                    f"{_EXAMPLE_BLOCK}\n{_NOTES_BLOCK}"
                ),
            },
        ],
    }
```

- [ ] **Step 5: Write the cloze model spec**

Create `spanish/models/cloze.py`:

```python
"""ES Cloze note type — fill-in-the-gap sentence cards (and grammar rows)."""
from spanish.models.styles import CARD_CSS

MODEL_NAME = "AnkiTransform ES Cloze"


def spec() -> dict:
    return {
        "modelName": MODEL_NAME,
        "inOrderFields": ["Text", "Translation", "Notes", "Source"],
        "isCloze": True,
        "css": CARD_CSS,
        "cardTemplates": [
            {
                "Name": "Cloze",
                "Front": '<div class="cloze-sentence">{{cloze:Text}}</div>',
                "Back": (
                    '<div class="cloze-sentence">{{cloze:Text}}</div>\n'
                    '{{#Translation}}<div class="example-de">{{Translation}}</div>{{/Translation}}\n'
                    '{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}\n'
                    '{{#Source}}<div class="source">📷 {{Source}}</div>{{/Source}}'
                ),
            }
        ],
    }
```

- [ ] **Step 6: Write the grammar model spec**

Create `spanish/models/grammar.py`:

```python
"""ES Grammar note type — reference card (title → full styled table)."""
from spanish.models.styles import CARD_CSS

MODEL_NAME = "AnkiTransform ES Grammar"


def spec() -> dict:
    return {
        "modelName": MODEL_NAME,
        "inOrderFields": ["Title", "Table_HTML", "Notes", "Source"],
        "isCloze": False,
        "css": CARD_CSS,
        "cardTemplates": [
            {
                "Name": "Grammar Table",
                "Front": '<div class="word">{{Title}}</div>',
                "Back": (
                    '{{FrontSide}}\n<hr id="answer">\n'
                    '<div class="table-wrap">{{Table_HTML}}</div>\n'
                    '{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}\n'
                    '{{#Source}}<div class="source">📷 {{Source}}</div>{{/Source}}'
                ),
            }
        ],
    }
```

- [ ] **Step 7: Write the package aggregator and CLI**

Create `spanish/models/__init__.py`:

```python
from spanish.models import vocab, cloze, grammar

ALL_MODELS = [vocab.spec(), cloze.spec(), grammar.spec()]

__all__ = ["ALL_MODELS", "vocab", "cloze", "grammar"]
```

Create `spanish/models/__main__.py`:

```python
import json

from spanish.models import ALL_MODELS

if __name__ == "__main__":
    print(json.dumps(ALL_MODELS, ensure_ascii=False, indent=2))
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run pytest tests/test_models.py -q`
Expected: PASS (5 passed)

- [ ] **Step 9: Commit**

```bash
git add spanish/models tests/test_models.py
git commit -m "feat(spanish): ES Vocab/Cloze/Grammar model specs + shared CSS"
```

---

### Task 4: `build_notes.py` — entries → AnkiConnect note payloads

**Files:**
- Create: `spanish/build_notes.py`
- Test: `tests/test_build_notes.py`

**Interfaces:**
- Consumes: `spanish.normalize.normalize` (Task 2); model names `AnkiTransform ES Vocab/Cloze/Grammar` (Task 3).
- Produces:
  - `cloze_to_plain(text: str) -> str` — strips `{{c<n>::answer}}` / `{{c<n>::answer::hint}}` markers down to `answer`.
  - `build_notes(data: dict) -> list[dict]` — each output note dict has keys: `model` (str), `deckName` (str), `fields` (dict), `tags` (list[str]), `dedup_key` (str), `dedup_field` (str).
  - `python -m … build_notes <cards.json> [--out FILE]` prints/writes the payload JSON and a stderr summary.
  - Input entry schema in `cards.json`:
    - vocab: `{type:"vocab", spanish, grammar, german, example_cloze, example_de, notes, source}`
    - grammar cloze: `{type:"grammar_cloze", title, rows:[[label, answer], …], table_html, source}`
    - grammar reference: `{type:"grammar_reference", title, table_html, notes, source}`

- [ ] **Step 1: Write the failing test**

Create `tests/test_build_notes.py`:

```python
from spanish.build_notes import build_notes, cloze_to_plain


def test_cloze_to_plain_strips_markers():
    assert cloze_to_plain("Por la {{c1::tarde}} estudio.") == "Por la tarde estudio."
    assert cloze_to_plain("a {{c2::b::hint}} c") == "a b c"


def test_vocab_produces_vocab_and_cloze_notes():
    data = {"deck_name": "D", "cards": [{
        "type": "vocab", "spanish": "la tarde", "grammar": "f",
        "german": "der Nachmittag",
        "example_cloze": "Por la {{c1::tarde}} estudio español.",
        "example_de": "Am Nachmittag lerne ich Spanisch.", "source": "a.jpg",
    }]}
    notes = build_notes(data)
    assert len(notes) == 2

    v = notes[0]
    assert v["model"] == "AnkiTransform ES Vocab"
    assert v["deckName"] == "D"
    assert v["fields"]["Spanish"] == "la tarde"
    assert v["fields"]["German"] == "der Nachmittag"
    assert v["fields"]["Example_ES"] == "Por la tarde estudio español."  # markers stripped
    assert v["dedup_key"] == "la tarde"
    assert v["dedup_field"] == "Spanish"

    c = notes[1]
    assert c["model"] == "AnkiTransform ES Cloze"
    assert c["fields"]["Text"] == "Por la {{c1::tarde}} estudio español."  # markers kept
    assert c["fields"]["Translation"] == "Am Nachmittag lerne ich Spanisch."
    assert c["dedup_field"] == "Text"


def test_vocab_without_example_has_no_cloze():
    data = {"cards": [{"type": "vocab", "spanish": "y", "german": "und"}]}
    notes = build_notes(data)
    assert len(notes) == 1
    assert notes[0]["model"] == "AnkiTransform ES Vocab"


def test_vocab_missing_german_is_skipped():
    data = {"cards": [{"type": "vocab", "spanish": "x"}]}
    assert build_notes(data) == []


def test_grammar_cloze_one_note_per_row():
    data = {"cards": [{
        "type": "grammar_cloze", "title": "ser",
        "rows": [["yo", "soy"], ["tú", "eres"]],
        "table_html": "<table></table>",
    }]}
    notes = build_notes(data)
    assert len(notes) == 2
    assert all(n["model"] == "AnkiTransform ES Cloze" for n in notes)
    assert notes[0]["fields"]["Text"] == "ser: yo → {{c1::soy}}"
    assert notes[1]["fields"]["Text"] == "ser: tú → {{c1::eres}}"
    assert notes[0]["fields"]["Notes"] == "<table></table>"


def test_grammar_reference_one_note():
    data = {"cards": [{
        "type": "grammar_reference", "title": "Alfabeto",
        "table_html": "<table></table>",
    }]}
    notes = build_notes(data)
    assert len(notes) == 1
    assert notes[0]["model"] == "AnkiTransform ES Grammar"
    assert notes[0]["fields"]["Title"] == "Alfabeto"
    assert notes[0]["dedup_key"] == "alfabeto"


def test_deck_name_defaults_when_absent():
    data = {"cards": [{"type": "vocab", "spanish": "y", "german": "und"}]}
    assert build_notes(data)[0]["deckName"] == "AnkiTransform::ES→DE::Lektion 0-1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_build_notes.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'spanish.build_notes'`

- [ ] **Step 3: Write the implementation**

Create `spanish/build_notes.py`:

```python
"""Convert authored cards.json entries into AnkiConnect note payloads.

Deterministic and fully tested. Claude authors the cards.json entries (extraction
+ example sentences); this module turns them into payloads with dedup keys, which
Claude then dedups (findNotes) and inserts (addNotes) via the anki-mcp-server.
"""
import argparse
import json
import re
import sys
from collections import Counter

from spanish.normalize import normalize

DEFAULT_DECK = "AnkiTransform::ES→DE::Lektion 0-1"

VOCAB_MODEL = "AnkiTransform ES Vocab"
CLOZE_MODEL = "AnkiTransform ES Cloze"
GRAMMAR_MODEL = "AnkiTransform ES Grammar"

_BASE_TAGS = ["ankitransform", "es"]
_CLOZE_RE = re.compile(r"\{\{c\d+::(.*?)(?:::.*?)?\}\}")


def cloze_to_plain(text: str) -> str:
    """Strip {{c1::answer}} / {{c1::answer::hint}} markers down to the answer."""
    return _CLOZE_RE.sub(r"\1", text)


def _g(card: dict, key: str) -> str:
    return str(card.get(key, "") or "").strip()


def _vocab(card: dict, deck: str) -> list[dict]:
    spanish = _g(card, "spanish")
    german = _g(card, "german")
    if not spanish or not german:
        return []

    example_cloze = _g(card, "example_cloze")
    example_de = _g(card, "example_de")
    notes_text = _g(card, "notes")
    source = _g(card, "source")

    out = [{
        "model": VOCAB_MODEL,
        "deckName": deck,
        "fields": {
            "Spanish": spanish,
            "Grammar": _g(card, "grammar"),
            "German": german,
            "Example_ES": cloze_to_plain(example_cloze),
            "Example_DE": example_de,
            "Notes": notes_text,
            "Source": source,
        },
        "tags": _BASE_TAGS,
        "dedup_key": normalize(spanish),
        "dedup_field": "Spanish",
    }]

    if "{{c" in example_cloze:
        out.append({
            "model": CLOZE_MODEL,
            "deckName": deck,
            "fields": {
                "Text": example_cloze,
                "Translation": example_de,
                "Notes": notes_text,
                "Source": source,
            },
            "tags": _BASE_TAGS + ["cloze"],
            "dedup_key": normalize(cloze_to_plain(example_cloze)),
            "dedup_field": "Text",
        })
    return out


def _grammar_cloze(card: dict, deck: str) -> list[dict]:
    title = _g(card, "title")
    table_html = _g(card, "table_html")
    source = _g(card, "source")
    out = []
    for row in card.get("rows", []):
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        label, answer = str(row[0]).strip(), str(row[1]).strip()
        if not label or not answer:
            continue
        text = f"{title}: {label} → {{{{c1::{answer}}}}}"
        out.append({
            "model": CLOZE_MODEL,
            "deckName": deck,
            "fields": {"Text": text, "Translation": "", "Notes": table_html, "Source": source},
            "tags": _BASE_TAGS + ["grammar"],
            "dedup_key": normalize(f"{title} {label}"),
            "dedup_field": "Text",
        })
    return out


def _grammar_reference(card: dict, deck: str) -> list[dict]:
    title = _g(card, "title")
    table_html = _g(card, "table_html")
    if not title or not table_html:
        return []
    return [{
        "model": GRAMMAR_MODEL,
        "deckName": deck,
        "fields": {
            "Title": title,
            "Table_HTML": table_html,
            "Notes": _g(card, "notes"),
            "Source": _g(card, "source"),
        },
        "tags": _BASE_TAGS + ["grammar"],
        "dedup_key": normalize(title),
        "dedup_field": "Title",
    }]


_BUILDERS = {
    "vocab": _vocab,
    "grammar_cloze": _grammar_cloze,
    "grammar_reference": _grammar_reference,
}


def build_notes(data: dict) -> list[dict]:
    deck = (data.get("deck_name") or DEFAULT_DECK).strip()
    out: list[dict] = []
    for card in data.get("cards", []):
        builder = _BUILDERS.get(card.get("type", "vocab"))
        if builder:
            out.extend(builder(card, deck))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="cards.json -> AnkiConnect note payloads")
    parser.add_argument("input", help="Path to cards.json")
    parser.add_argument("--out", default="-", help="Output path, or '-' for stdout")
    args = parser.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    notes = build_notes(data)
    payload = json.dumps(notes, ensure_ascii=False, indent=2)

    if args.out == "-":
        print(payload)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)

    counts = Counter(n["model"] for n in notes)
    print(f"[build_notes] {len(notes)} notes -> {dict(counts)}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_build_notes.py -q`
Expected: PASS (7 passed)

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -q`
Expected: PASS (16 passed total).

- [ ] **Step 6: Commit**

```bash
git add spanish/build_notes.py tests/test_build_notes.py
git commit -m "feat(spanish): build_notes() — cards.json entries to Anki note payloads"
```

---

### Task 5: MCP + AnkiConnect setup, model creation, live-deck inspection

> This task wires up the live Anki connection. It requires the Anki desktop app to be **running** with the AnkiConnect add-on installed, and a Claude Code restart so the MCP server loads. Verification steps are interactive (MCP tool calls) rather than unit tests.

**Files:**
- Create: `.mcp.json`

**Interfaces:**
- Consumes: `python -m spanish.models` (Task 3) for the `createModel` params.
- Produces: three note types present in Anki; a verified `anki-mcp` MCP connection; notes on the live deck's existing layout recorded in the run report.

- [ ] **Step 1: Create `.mcp.json`**

Create `.mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "anki-mcp": {
      "command": "npx",
      "args": ["-y", "@ankimcp/anki-mcp-server", "--stdio"],
      "env": {
        "ANKI_CONNECT_URL": "http://localhost:8765"
      }
    }
  }
}
```

- [ ] **Step 2: Install AnkiConnect (manual, user)**

In Anki: **Tools → Add-ons → Get Add-ons…**, paste code `2055492159`, restart Anki. Leave Anki running.

Verify from a terminal:
Run: `curl -s -m 3 localhost:8765 -X POST -d '{"action":"version","version":6}'`
Expected: JSON like `{"result": 6, "error": null}`.

- [ ] **Step 3: Load the MCP server (manual, user)**

Restart Claude Code in this project so `.mcp.json` is picked up, and approve the `anki-mcp` server when prompted.

- [ ] **Step 4: Verify the MCP connection**

Call the MCP tool `listDecks` (via the `anki-mcp` server).
Expected: a list of deck names including the existing Spanish deck. If it errors, Anki isn't running / AnkiConnect not installed — fix before continuing.

- [ ] **Step 5: Inspect the live Spanish deck**

- Call `findNotes` with query `deck:"AnkiTransform::ES→DE::Lektion 0-1"` (adjust to the real deck name from Step 4).
- Call `notesInfo` on ~5 returned note IDs.
- Record in the report: the existing note type/field names, and any quality issues worth improving. This satisfies the spec's "inspect the current live deck before finalizing."

- [ ] **Step 6: Create the three note types in Anki**

Run: `uv run python -m spanish.models`
For each of the three objects in the printed JSON, call the MCP `createModel` tool with that object's `modelName`, `inOrderFields`, `css`, `isCloze`, and `cardTemplates`.

Verify: call `modelNames` and confirm `AnkiTransform ES Vocab`, `AnkiTransform ES Cloze`, `AnkiTransform ES Grammar` are present.

- [ ] **Step 7: Smoke-test one note end to end**

- Hand-write a tiny `spanish/cards.json` with one vocab entry (spanish/german/example_cloze/example_de).
- Run: `uv run python -m spanish.build_notes spanish/cards.json`
- Take the first payload, call `findNotes` on its `dedup_key` (expect empty), then `addNote` with its `model`/`deckName`/`fields`/`tags`.
- Open Anki, confirm the card renders with correct styling on both templates. Then delete the test note (`deleteNotes`) and restore `cards.json` to an empty `cards: []`.

- [ ] **Step 8: Commit**

```bash
git add .mcp.json
git commit -m "chore: register anki-mcp-server (AnkiConnect) for the Spanish pipeline"
```

---

### Task 6: The `/spanish` orchestration skill + docs

**Files:**
- Create: `.claude/skills/spanish/SKILL.md`
- Create: `spanish/README.md`
- Create: `spanish/upgrade_legacy.md`

**Interfaces:**
- Consumes: everything from Tasks 1–5 (folders, `build_notes`, models, MCP tools).
- Produces: a documented, repeatable procedure invocable as `/spanish` or by plain-language request.

- [ ] **Step 1: Write the skill**

Create `.claude/skills/spanish/SKILL.md`:

````markdown
---
name: spanish
description: Turn Spanish textbook photos in spanish/inbox/ into well-styled Anki cards and push them straight into the live deck via the anki-mcp MCP server. Trigger with /spanish or "run the Spanish pipeline".
---

# Spanish Anki Pipeline

Turn textbook photos into live Anki cards. **You do all the work**; the user only drops photos and triggers you.

## Hard rules
- **Terms are extracted faithfully** from the photo — never invent vocab or grammar content.
- **Example sentences ARE generated by you**: short, level-appropriate, using the target word naturally, always with a German gloss. If unsure a sentence is correct, flag it in the report rather than guessing.
- **All Anki writes go through the `anki-mcp` MCP tools.** Never POST to AnkiConnect directly.
- **Never delete or modify existing notes.** This pipeline only adds.

## Procedure

1. **Preflight.** Call `listDecks`. If it errors, stop and tell the user: "Open Anki (with AnkiConnect) and try again." Confirm the three models exist via `modelNames`; if any are missing, create them from `uv run python -m spanish.models` (see Task 5 / setup).

2. **Read photos.** For each image in `spanish/inbox/`, read it directly with vision. Vocab pages: extract Spanish–German pairs (note gender/POS as the `grammar` tag). Grammar pages: read the table; decide reference vs. drillable (conjugation/declension → cloze rows; alphabet/pronunciation/rule lists → reference).

3. **Author `spanish/cards.json`.** Append entries using this schema:
   - vocab: `{"type":"vocab","spanish":"la tarde","grammar":"f","german":"der Nachmittag","example_cloze":"Por la {{c1::tarde}} estudio español.","example_de":"Am Nachmittag lerne ich Spanisch.","notes":"","source":"IMG_x.jpeg"}`
   - grammar (drill): `{"type":"grammar_cloze","title":"Konjugation von ser","rows":[["yo","soy"],["tú","eres"]],"table_html":"<table>…</table>","source":"IMG_y.jpeg"}`
   - grammar (reference): `{"type":"grammar_reference","title":"El alfabeto","table_html":"<table>…</table>","notes":"","source":"IMG_z.jpeg"}`
   - The cloze deletion (`{{c1::…}}`) goes on the **target word's form as it appears in the sentence**.

4. **Build payloads.** Run `uv run python -m spanish.build_notes spanish/cards.json --out spanish/.payload.json`.

5. **Dedup against the live deck.** For each payload, `findNotes` with query `deck:"<deckName>" <DedupField>:"<dedup_key text>"` (use the payload's `dedup_field`). Drop any payload that already matches. Keep a running skipped count.

6. **Insert.** `addNotes` the survivors in batches ≤100 (`model`→modelName, `deckName`, `fields`, `tags`). Cloze notes use the `AnkiTransform ES Cloze` model.

7. **Archive + log.** Move processed photos from `spanish/inbox/` to `spanish/archive/`. Leave the appended entries in `spanish/cards.json` as the audit log. Delete `spanish/.payload.json`.

8. **Report.** Print: cards added per type, duplicates skipped, photos archived, and any low-confidence example sentences or unreadable spots you skipped (ask the user about those).

## Notes
- The default deck name is in `spanish/cards.json` (`deck_name`). Confirm it matches a real deck from `listDecks`; if not, ask which deck to use.
- If a photo is ambiguous, ask the user rather than guessing.
````

- [ ] **Step 2: Write `spanish/README.md`**

```markdown
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
- `inbox/` — drop new photos here.
- `archive/` — processed photos land here automatically.
- `models/` — note-type definitions (fields, templates, CSS) = source of truth.
- `cards.json` — running audit log of authored cards (new schema).
- `cards.legacy.json` — the original 439 v1 cards, preserved for the optional upgrade.
- `build_notes.py` / `normalize.py` — deterministic, tested transform + dedup helpers.
```

- [ ] **Step 3: Write `spanish/upgrade_legacy.md` (deferred, optional procedure)**

```markdown
# Optional: upgrade the legacy 439 cards (non-destructive)

Out of scope for the initial build. When you want the old Lektion 0-1 cards in the new
Recognition + Production + Cloze format **without losing review history**:

1. Read `spanish/cards.legacy.json` (old schema: `front`/`back`/`grammar`/`notes`, types
   `vocab` / `grammar_table`).
2. For each entry, author a new-schema entry in `spanish/cards.json`: map `front`→`spanish`,
   `back`→`german`, `grammar`→`grammar`; generate an `example_cloze` + `example_de`. Convert
   `grammar_table` entries to `grammar_cloze`/`grammar_reference`.
3. Run the normal `/spanish` pipeline — dedup will skip anything already present, so only the
   new cloze/production cards get added.
4. **Do not delete** the originals. If you want them out of rotation, **suspend** them in Anki
   (select in Browser → right-click → Toggle Suspend). Never `deleteNotes` the legacy cards.
```

- [ ] **Step 4: Verify the skill is discoverable**

Run: `ls .claude/skills/spanish/SKILL.md`
Expected: the path exists. (After a Claude Code restart, `/spanish` resolves to this skill.)

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/spanish/SKILL.md spanish/README.md spanish/upgrade_legacy.md
git commit -m "feat(spanish): /spanish orchestration skill + docs"
```

---

## Self-Review

**Spec coverage:**
- Repo layout (two top-level folders) → Task 1. ✓
- Vision-first, drop Tesseract → Task 1 (delete) + Task 6 (skill reads photos). ✓
- 3-card vocab (Recognition+Production+Cloze) → Task 3 (models) + Task 4 (build_notes). ✓
- Grammar hybrid (cloze rows vs reference) → Task 3 + Task 4 (`grammar_cloze`/`grammar_reference`). ✓
- Direct-to-deck via MCP, no `.apkg` → Task 5 + Task 6. ✓
- Dedup via live `findNotes` → Task 6 (uses `dedup_key`/`dedup_field` from Task 4). ✓
- Existing cards preserved + optional upgrade → Task 1 (`cards.legacy.json`) + Task 6 (`upgrade_legacy.md`). ✓
- Reuse CSS/styling → Task 3 (`styles.py`). ✓
- Remove dedup_cards.py, ocr_extract.py, Copilot agent, CLI subcommands → Task 1. ✓
- Setup (AnkiConnect + .mcp.json + inspect live deck) → Task 5. ✓

**Placeholder scan:** No TBD/TODO; every code step shows full code; commands have expected output.

**Type consistency:** Model names identical across Tasks 3/4/5/6 (`AnkiTransform ES Vocab/Cloze/Grammar`). `build_notes()` output keys (`model`, `deckName`, `fields`, `tags`, `dedup_key`, `dedup_field`) are consumed unchanged by the Task 6 skill. `normalize()` signature matches its use in Task 4. cards.json entry schema is identical in Task 4 interface and Task 6 skill.

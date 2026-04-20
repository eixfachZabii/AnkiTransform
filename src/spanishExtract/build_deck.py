"""
build_deck.py — Anki deck builder from extracted vocabulary JSON
----------------------------------------------------------------
Usage:
    python build_deck.py <cards.json> [--deck-name "Spanish Vocab"] [--out deck.apkg]

Input JSON schema (produced by agent via AGENT.md):
    {
      "deck_name": "AnkiTransform::ES→DE::Lektion 1",
      "lang_front": "es",
      "lang_back": "de",
      "cards": [
        { "type": "vocab",         "front": "1. la tarde", "back": "Nachmittag", "grammar": "f", "notes": "" },
        { "type": "grammar_table", "front": "1. Deklination Artikel", "back_html": "<table>...</table>", "notes": "" }
      ],
      "recognition_issues": []
    }
"""

import genanki
import json
import argparse
import sys
import html
from pathlib import Path
from datetime import datetime


# ── Model definition ──────────────────────────────────────────────────────────
# Stable model ID — never change or existing cards will duplicate on re-import
MODEL_ID = 1876543210

ANKI_MODEL = genanki.Model(
    MODEL_ID,
    "AnkiTransform Spanish",
    fields=[
        {"name": "Front"},    # Spanish word/phrase or grammar table title
        {"name": "Grammar"},  # e.g. "f", "m", "inf", "pl" — empty for tables
        {"name": "Back"},     # Translation or HTML table
        {"name": "Notes"},    # Extra context / conjugation hints
        {"name": "Source"},   # Source image filename for traceability
    ],
    templates=[
        {
            "name": "ES → Translation",
            "qfmt": """
<div class="word">{{Front}}</div>
{{#Grammar}}<div class="grammar">{{Grammar}}</div>{{/Grammar}}
""",
            "afmt": """
{{FrontSide}}
<hr id="answer">
<div class="translation">{{Back}}</div>
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
<div class="source">📷 {{Source}}</div>
""",
        },
        {
            "name": "Translation → ES",
            "qfmt": """
<div class="word">{{Back}}</div>
{{#Grammar}}<div class="grammar">{{Grammar}}</div>{{/Grammar}}
""",
            "afmt": """
{{FrontSide}}
<hr id="answer">
<div class="word">{{Front}}</div>
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
""",
        },
    ],
    css="""
.card {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 24px;
    text-align: center;
    color: #1a1a2e;
    background: #f8f9fa;
    padding: 20px;
}
.word {
    font-size: 32px;
    font-weight: 600;
    margin: 20px 0;
    color: #16213e;
}
.grammar {
    display: inline-block;
    background: #e63946;
    color: white;
    font-size: 13px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 12px;
    margin-bottom: 12px;
    letter-spacing: 0.5px;
    text-transform: lowercase;
}
.translation {
    font-size: 28px;
    font-weight: 500;
    color: #0f3460;
    margin: 16px 0;
}
.notes {
    font-size: 15px;
    color: #666;
    font-style: italic;
    margin-top: 10px;
    padding: 8px 16px;
    background: #e9ecef;
    border-radius: 8px;
    display: inline-block;
}
.source {
    font-size: 11px;
    color: #aaa;
    margin-top: 20px;
}
hr#answer {
    border: none;
    border-top: 1px solid #dee2e6;
    margin: 20px 0;
}

/* ── Grammar table styles ── */
table.grammar {
    border-collapse: collapse;
    margin: 16px auto;
    font-size: 18px;
    min-width: 300px;
}
table.grammar th {
    background: #16213e;
    color: white;
    padding: 8px 14px;
    font-weight: 600;
    text-align: center;
}
table.grammar td {
    border: 1px solid #dee2e6;
    padding: 7px 14px;
    text-align: center;
    color: #1a1a2e;
}
table.grammar tr:nth-child(even) td {
    background: #e9ecef;
}
table.grammar td b {
    color: #e63946;
}
""",
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path: str) -> dict:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def make_note(card: dict, source_name: str) -> genanki.Note | None:
    card_type = card.get("type", "vocab")

    if card_type == "grammar_table":
        front   = html.escape(card.get("front", "").strip())
        grammar = ""
        back    = card.get("back_html", "").strip()   # raw HTML — do not escape
        notes   = html.escape(card.get("notes", "").strip())
        if not front or not back:
            return None

    else:  # vocab (default)
        front   = html.escape(card.get("front", "").strip())
        grammar = html.escape(card.get("grammar", "").strip())
        back    = html.escape(card.get("back", "").strip())
        notes   = html.escape(card.get("notes", "").strip())
        if not front or not back:
            return None

    return genanki.Note(
        model=ANKI_MODEL,
        fields=[front, grammar, back, notes, source_name],
        guid=genanki.guid_for(front, back),  # stable: re-import updates, not duplicates
    )


def build_deck(data: dict, deck_name: str) -> genanki.Deck:
    deck_id      = abs(hash(deck_name)) % (10**10)
    deck         = genanki.Deck(deck_id, deck_name)
    source_name  = Path(data.get("source_image", "")).name or ""
    cards        = data.get("cards", [])

    vocab_count   = 0
    table_count   = 0
    skipped_count = 0

    for card in cards:
        note = make_note(card, source_name)
        if note is None:
            skipped_count += 1
            continue
        deck.add_note(note)
        if card.get("type") == "grammar_table":
            table_count += 1
        else:
            vocab_count += 1

    print(f"[build] Vocab cards:   {vocab_count}", file=sys.stderr)
    print(f"[build] Grammar tables: {table_count}", file=sys.stderr)
    if skipped_count:
        print(f"[build] Skipped (missing front/back): {skipped_count}", file=sys.stderr)

    # Print recognition issues if present
    issues = data.get("recognition_issues", [])
    if issues:
        print(f"\n[build] ⚠️  Recognition issues reported by agent ({len(issues)}):", file=sys.stderr)
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. [{issue.get('location', '?')}] {issue.get('problem', '?')}", file=sys.stderr)
            print(f"     Skipped: {issue.get('what_was_skipped', '?')}", file=sys.stderr)

    return deck


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build an Anki .apkg deck from agent-extracted vocabulary JSON."
    )
    parser.add_argument("input", help="Path to cards.json, or '-' for stdin")
    parser.add_argument("--deck-name", default=None, help="Override deck name")
    parser.add_argument("--out",       default=None, help="Output .apkg path")
    args = parser.parse_args()

    try:
        data = load_json(args.input)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[build] ERROR loading input: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine deck name: CLI arg > JSON field > fallback
    deck_name = (
        args.deck_name
        or data.get("deck_name")
        or f"AnkiTransform::{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    deck = build_deck(data, deck_name)

    if len(deck.notes) == 0:
        print("[build] ERROR: No valid cards found. Check your JSON.", file=sys.stderr)
        sys.exit(1)

    out_path = args.out or f"{deck_name.replace('::', '_').replace(' ', '_')}.apkg"
    genanki.Package(deck).write_to_file(out_path)
    print(f"\n[build] ✓ Saved: {out_path}", file=sys.stderr)
    print(f"[build]   Anki: File → Import → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
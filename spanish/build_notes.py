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

# Which target deck each card type routes to. Vocab (and the cloze sentence it
# spawns) follow the word into the vocab deck; grammar drills and reference
# tables go to the grammar deck.
_TYPE_DECK = {
    "vocab": "vocab",
    "grammar_cloze": "grammar",
    "grammar_reference": "grammar",
}


def _decks(data: dict) -> dict[str, str]:
    """Resolve the per-type deck map, falling back to a single deck_name/default."""
    fallback = (data.get("deck_name") or DEFAULT_DECK).strip()
    decks = data.get("decks") or {}
    return {
        "vocab": (decks.get("vocab") or fallback).strip(),
        "grammar": (decks.get("grammar") or fallback).strip(),
    }


def build_notes(data: dict) -> list[dict]:
    decks = _decks(data)
    out: list[dict] = []
    for card in data.get("cards", []):
        card_type = card.get("type", "vocab")
        builder = _BUILDERS.get(card_type)
        if builder:
            deck = decks[_TYPE_DECK.get(card_type, "vocab")]
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

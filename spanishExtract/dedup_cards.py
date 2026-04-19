"""
dedup_cards.py — Remove duplicate cards from cards.json

Detects duplicates by normalizing the front field (strip prefix number,
lowercase, strip whitespace) and keeps the first occurrence.

Usage:
    python dedup_cards.py cards.json
"""
import json
import re
import sys
import unicodedata


def normalize(text: str) -> str:
    """Normalize text for comparison: strip lektion prefix, lowercase, collapse whitespace."""
    # Remove lektion prefix like "0. " or "1. "
    text = re.sub(r'^\d+\.\s*', '', text)
    # Normalize unicode
    text = unicodedata.normalize('NFC', text)
    # Lowercase and strip
    text = text.lower().strip()
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text


def dedup(input_path: str, output_path: str = None):
    if output_path is None:
        output_path = input_path

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    seen = set()
    unique_cards = []
    removed = []

    for card in data['cards']:
        if card['type'] == 'grammar_table':
            key = normalize(card.get('front', '')) + '||TABLE'
        else:
            key = normalize(card.get('front', '')) + '||' + normalize(card.get('back', ''))

        if key in seen:
            removed.append(card.get('front', ''))
            continue

        seen.add(key)
        unique_cards.append(card)

    data['cards'] = unique_cards

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Cards before: {len(unique_cards) + len(removed)}")
    print(f"Cards after:  {len(unique_cards)}")
    print(f"Removed:      {len(removed)} duplicates")
    if removed:
        for r in removed[:10]:
            print(f"  - {r}")
        if len(removed) > 10:
            print(f"  ... and {len(removed) - 10} more")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "cards.json"
    dedup(path)


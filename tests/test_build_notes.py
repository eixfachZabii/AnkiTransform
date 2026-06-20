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

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

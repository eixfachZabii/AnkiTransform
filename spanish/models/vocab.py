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

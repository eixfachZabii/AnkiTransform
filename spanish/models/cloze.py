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

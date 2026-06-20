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

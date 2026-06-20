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

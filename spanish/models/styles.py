"""Shared card CSS — single source of truth for all AnkiTransform ES note types.

Themed with CSS custom properties so a single palette drives every component.
Dark mode is handled two ways for full coverage:
  - `.nightMode` — Anki desktop's night-mode toggle.
  - `@media (prefers-color-scheme: dark)` — AnkiMobile / AnkiDroid / AnkiWeb
    that follow the system theme.
"""

CARD_CSS = """
/* ---- palette (light) ---- */
.card {
    --bg: #fbfbfd;
    --fg: #1c1f2a;
    --muted: #71757f;
    --heading: #16203a;
    --accent: #e5484d;       /* grammar chip, cloze gap */
    --accent-soft: rgba(229,72,77,0.12);
    --link: #3b6fd4;         /* translation */
    --panel: #ffffff;
    --panel-2: #f1f3f8;      /* example box */
    --border: #e6e8ee;
    --shadow: 0 1px 2px rgba(18,22,33,0.04), 0 8px 24px rgba(18,22,33,0.06);
    --th-bg: #16203a;        /* table header */
    --th-fg: #ffffff;

    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 22px;
    line-height: 1.5;
    text-align: center;
    color: var(--fg);
    background: var(--bg);
    padding: 30px 18px;
    -webkit-font-smoothing: antialiased;
}

/* ---- palette (dark) ---- */
.nightMode.card, .nightMode .card {
    --bg: #15171c;
    --fg: #e6e8ee;
    --muted: #969bab;
    --heading: #eaf0fb;
    --accent: #ff7a85;
    --accent-soft: rgba(255,122,133,0.16);
    --link: #82a9f9;
    --panel: #1e222b;
    --panel-2: #242a35;
    --border: #30353f;
    --shadow: 0 1px 2px rgba(0,0,0,0.4), 0 10px 28px rgba(0,0,0,0.45);
    --th-bg: #2a3550;        /* table header */
    --th-fg: #eaf0fb;
}
@media (prefers-color-scheme: dark) {
    .card {
        --bg: #15171c;
        --fg: #e6e8ee;
        --muted: #969bab;
        --heading: #eaf0fb;
        --accent: #ff7a85;
        --accent-soft: rgba(255,122,133,0.16);
        --link: #82a9f9;
        --panel: #1e222b;
        --panel-2: #242a35;
        --border: #30353f;
        --shadow: 0 1px 2px rgba(0,0,0,0.4), 0 10px 28px rgba(0,0,0,0.45);
    }
}

/* ---- components ---- */
.direction {
    font-size: 11px; font-weight: 700; color: var(--muted);
    text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 14px;
}
.word { font-size: 34px; font-weight: 700; margin: 10px 0; color: var(--heading); letter-spacing: -0.2px; }
div.grammar {
    display: inline-block; background: var(--accent-soft); color: var(--accent);
    font-size: 13px; font-weight: 700; padding: 4px 12px; border-radius: 999px;
    margin-top: 10px; letter-spacing: 0.3px; text-transform: lowercase;
}
.translation { font-size: 28px; font-weight: 600; color: var(--link); margin: 14px 0; }
.example {
    font-size: 18px; color: var(--fg); margin: 18px auto; max-width: 92%;
    padding: 14px 18px; background: var(--panel-2); border-radius: 14px;
    border-left: 3px solid var(--accent); text-align: left; box-shadow: var(--shadow);
}
.example-de { display: block; margin-top: 6px; font-size: 15px; color: var(--muted); font-style: italic; }
.notes {
    font-size: 15px; color: var(--muted); margin-top: 14px;
    padding: 9px 16px; background: var(--panel); border: 1px solid var(--border);
    border-radius: 12px; display: inline-block;
}
.source { font-size: 11px; color: var(--muted); margin-top: 22px; opacity: 0.8; }
hr#answer { border: none; border-top: 1px solid var(--border); margin: 22px 0; }

/* cloze */
.cloze-sentence { font-size: 24px; color: var(--heading); margin: 18px auto; max-width: 92%; }
.cloze { font-weight: 800; color: var(--accent); }

/* hover hint */
.hint { position: relative; display: inline; cursor: help; }
.hint .cloze { border-bottom: 1px dotted var(--accent); }
.hint::after {
    content: attr(data-hint);
    position: absolute;
    left: 50%;
    bottom: 100%;
    transform: translateX(-50%) translateY(-8px);
    background: var(--panel);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: var(--shadow);
    padding: 6px 10px;
    font-size: 14px;
    font-weight: 600;
    white-space: nowrap;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.15s ease;
    pointer-events: none;
    z-index: 10;
}
.hint:hover::after {
    opacity: 1;
    visibility: visible;
}

/* grammar tables + images */
.table-wrap { margin: 16px auto; overflow-x: auto; }
.table-wrap img { max-width: 100%; height: auto; border-radius: 12px; box-shadow: var(--shadow); }
table {
    border-collapse: separate; border-spacing: 0; margin: 16px auto; font-size: 17px;
    min-width: 280px; border-radius: 10px; overflow: hidden; box-shadow: var(--shadow);
}
table th { background: var(--th-bg); color: var(--th-fg); padding: 10px 16px; font-weight: 600; }
table td { border-top: 1px solid var(--border); padding: 9px 16px; color: var(--fg); }
table tr:nth-child(even) td { background: var(--panel-2); }
table td b, table td strong { color: var(--accent); }
""".strip()

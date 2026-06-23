# Cloze Hover-Hint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hovering the `[...]` gap on a Spanish vocab cloze card shows the target word's German translation as a tooltip, without leaking the answer by default.

**Architecture:** Wrap the existing `{{c1::word}}` cloze marker in `<span class="hint" data-hint="German">...</span>` at authoring time. Pure CSS (`content: attr(data-hint)` + `:hover`) renders a themed tooltip bubble — no JS, no `build_notes.py` changes, since its regex only touches the `{{c1::...}}` token and ignores surrounding HTML.

**Tech Stack:** Python 3.10+, pytest, Anki via `anki-mcp` MCP tools (AnkiConnect), Playwright MCP for visual preview screenshots.

## Global Constraints

- Scope: vocab cloze cards only (notes tagged `cloze`, model `AnkiTransform ES Cloze`). Grammar conjugation-drill cloze notes (tagged `grammar`) are out of scope and must not be touched.
- Platform: Anki Desktop only. Pure CSS `:hover` — no JavaScript, no tap/touch support.
- `[...]` must remain the default visible state; the hint only appears on `:hover`.
- One cloze deletion (`{{c1::...}}`) per vocab example sentence — no multi-cloze support needed.
- All theming uses the existing CSS custom properties already defined on `.card` in `spanish/models/styles.py` (`--accent`, `--panel`, `--border`, `--shadow`, `--fg`) — both the `.nightMode` block and the `prefers-color-scheme: dark` media query must work, per existing convention.
- Never modify `build_notes.py`'s cloze-matching regex behavior — only add a regression test confirming the wrapper passes through untouched.

---

### Task 1: Regression test — confirm `build_notes.py` passes the hint wrapper through unchanged

**Files:**
- Modify: `tests/test_build_notes.py`

**Interfaces:**
- Consumes: `spanish.build_notes.build_notes` (existing, unchanged signature: `build_notes(data: dict) -> list[dict]`).
- Produces: nothing new — this is a characterization test locking in current behavior so a future regex change can't silently break the wrapper passthrough.

- [ ] **Step 1: Write the test**

Add to `tests/test_build_notes.py`:

```python
def test_hint_wrapper_passes_through_unchanged():
    cloze_text = (
        'Tengo dos <span class="hint" data-hint="Brüder">{{c1::hermanos}}</span>.'
    )
    data = {"cards": [{
        "type": "vocab", "spanish": "el hermano", "german": "der Bruder",
        "example_cloze": cloze_text,
        "example_de": "Ich habe zwei Brüder.", "source": "a.jpg",
    }]}
    notes = build_notes(data)
    assert len(notes) == 2

    vocab_note, cloze_note = notes
    assert vocab_note["fields"]["Example_ES"] == (
        'Tengo dos <span class="hint" data-hint="Brüder">hermanos</span>.'
    )
    assert cloze_note["fields"]["Text"] == cloze_text
```

- [ ] **Step 2: Run it and confirm it passes immediately**

Run: `uv run pytest tests/test_build_notes.py::test_hint_wrapper_passes_through_unchanged -v`
Expected: **PASS** with no code changes. (Unlike normal TDD, there's no red step here — this test exists to *prove* `build_notes.py` already handles the new authoring convention correctly, per the design's "why no code changes" rationale.) If it fails, do not "fix" `build_notes.py` to match — stop and re-examine the design, since the whole point of the wrapper approach is that it needs zero changes there.

- [ ] **Step 3: Commit**

```bash
git add tests/test_build_notes.py
git commit -m "test(spanish): lock in hint-wrapper passthrough in build_notes"
```

---

### Task 2: Add the hover-hint tooltip CSS to the shared card stylesheet

**Files:**
- Modify: `spanish/models/styles.py`
- Modify: `tests/test_models.py`

**Interfaces:**
- Consumes: existing CSS custom properties on `.card` (`--accent`, `--panel`, `--fg`, `--border`, `--shadow`).
- Produces: `.hint` / `.hint::after` / `.hint:hover::after` selectors in `CARD_CSS`, which Task 3's preview and Task 5's live push both depend on by name.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
def test_cloze_css_has_hover_hint_tooltip():
    css = cloze.spec()["css"]
    assert ".hint {" in css
    assert "content: attr(data-hint)" in css
    assert ".hint:hover::after" in css
    assert "var(--panel)" in css and "var(--accent)" in css
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_models.py::test_cloze_css_has_hover_hint_tooltip -v`
Expected: FAIL — `assert ".hint {" in css` is False (the rule doesn't exist yet).

- [ ] **Step 3: Add the CSS**

In `spanish/models/styles.py`, immediately after the existing `/* cloze */` block (the lines `.cloze-sentence { ... }` / `.cloze { ... }`), insert:

```css
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
```

This must land *inside* the triple-quoted `CARD_CSS` string (before the closing `""".strip()`), so it ships to all three models that share `CARD_CSS`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_models.py::test_cloze_css_has_hover_hint_tooltip -v`
Expected: PASS

- [ ] **Step 5: Run the full test suite to check for regressions**

Run: `uv run pytest tests/ -v`
Expected: all tests PASS (including Task 1's new test and all pre-existing tests).

- [ ] **Step 6: Commit**

```bash
git add spanish/models/styles.py tests/test_models.py
git commit -m "feat(spanish): add hover-hint tooltip CSS for vocab cloze cards"
```

---

### Task 3: Update the `/spanish` skill's authoring schema for new cards

**Files:**
- Modify: `.claude/skills/spanish/SKILL.md`

**Interfaces:**
- Consumes: nothing (documentation only).
- Produces: the authoring convention that Task 1's wrapper format depends on going forward — every new `example_cloze` written by the `/spanish` pipeline must use this exact wrapper syntax.

- [ ] **Step 1: Update the vocab schema example**

In `.claude/skills/spanish/SKILL.md`, find this line (currently line 23):

```
   - vocab: `{"type":"vocab","spanish":"la tarde","grammar":"f","german":"der Nachmittag","example_cloze":"Por la {{c1::tarde}} estudio español.","example_de":"Am Nachmittag lerne ich Spanisch.","notes":"","source":"IMG_x.jpeg"}`
```

Replace it with:

```
   - vocab: `{"type":"vocab","spanish":"la tarde","grammar":"f","german":"der Nachmittag","example_cloze":"Por la <span class=\"hint\" data-hint=\"Nachmittag\">{{c1::tarde}}</span> estudio español.","example_de":"Am Nachmittag lerne ich Spanisch.","notes":"","source":"IMG_x.jpeg"}`
```

- [ ] **Step 2: Add the hint-wrapper rule**

Find this line (currently line 26):

```
   - The cloze deletion (`{{c1::…}}`) goes on the **target word's form as it appears in the sentence**.
```

Immediately after it, add a new bullet:

```
   - Wrap the cloze marker in `<span class="hint" data-hint="...">{{c1::word}}</span>`, where `data-hint` is the German translation **in the exact inflected form used in the sentence** (e.g. `data-hint="Brüder"` for a plural example, not the dictionary singular "Bruder"). This drives a hover tooltip — see the `.hint` rules in `spanish/models/styles.py`. Grammar cloze cards (`grammar_cloze` type) do **not** get this wrapper.
```

- [ ] **Step 3: Verify the edit**

Run: `grep -n "data-hint" .claude/skills/spanish/SKILL.md`
Expected: two matches — the updated schema example and the new rule bullet.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/spanish/SKILL.md
git commit -m "docs(spanish): require hint-wrapper syntax for new vocab cloze cards"
```

---

### Task 4: Render a light/dark preview and get sign-off before touching live data

**Files:**
- Create: a scratch HTML file in your scratchpad directory (not committed — this is a throwaway visual check, not project code).
- Create: `.playwright/screenshots/cloze-hover-hint-light.png`
- Create: `.playwright/screenshots/cloze-hover-hint-dark.png`
- Create: `.playwright/screenshots/cloze-hover-hint-hover.png`

**Interfaces:**
- Consumes: `spanish.models.styles.CARD_CSS` (must be the version with Task 2's `.hint` rules already merged in).
- Produces: nothing code-facing — this task's only output is three screenshots and an explicit user approval, which gates Task 5.

- [ ] **Step 1: Generate the preview HTML**

Run this in a Python one-liner (or a throwaway script in your scratchpad dir) to dump current `CARD_CSS` plus a sample card into an HTML file — substitute `<scratchpad>` with your actual scratchpad directory path:

```bash
uv run python -c "
from spanish.models.styles import CARD_CSS
html = f'''<!DOCTYPE html>
<html><head><meta charset=\"utf-8\"><style>
{CARD_CSS}
body {{ margin: 0; padding: 40px; font-family: sans-serif; }}
.demo {{ display: inline-block; margin: 20px; vertical-align: top; }}
</style></head><body>
<div class=\"demo\"><div class=\"card\">
  <div class=\"cloze-sentence\">Tengo dos <span class=\"hint\" data-hint=\"Brüder\"><span class=\"cloze\">[...]</span></span>.</div>
</div></div>
<div class=\"demo nightMode\"><div class=\"card\">
  <div class=\"cloze-sentence\">Tengo dos <span class=\"hint\" data-hint=\"Brüder\"><span class=\"cloze\">[...]</span></span>.</div>
</div></div>
</body></html>'''
open('<scratchpad>/cloze-hover-preview.html', 'w').write(html)
"
```

- [ ] **Step 2: Screenshot the default (un-hovered) state**

Use the Playwright MCP tools: navigate to `file://<scratchpad>/cloze-hover-preview.html`, then take a full-page screenshot saved to `.playwright/screenshots/cloze-hover-hint-light.png`. Confirm both the light card (left) and the `.nightMode` card (right) show `[...]` with a dotted underline, no tooltip visible.

- [ ] **Step 3: Screenshot the hover state**

With the same page still open, hover over the `.cloze` element inside the light-mode card, then take a screenshot saved to `.playwright/screenshots/cloze-hover-hint-hover.png`. Confirm the tooltip bubble "Brüder" appears above the gap, styled with the card's panel/border/shadow colors.

- [ ] **Step 4: Screenshot the dark-mode hover state**

Hover over the `.cloze` element inside the `.nightMode` card, then take a screenshot saved to `.playwright/screenshots/cloze-hover-hint-dark.png`. Confirm the tooltip is legible against the dark palette (uses the `.nightMode` CSS variable overrides, not the light ones).

- [ ] **Step 5: STOP — get explicit user approval**

Show the three screenshots to the user and ask whether the tooltip's look (position, sizing, colors, dotted-underline affordance) is acceptable. **Do not proceed to Task 5 or Task 6 until the user explicitly approves.** If they request visual changes, go back to Task 2's CSS, adjust, and re-run this task's screenshots.

---

### Task 5: Push the updated CSS to the live Anki models

**Preconditions:** Task 4 approved. Anki is running with AnkiConnect.

**Files:** none (this task only calls MCP tools against the live Anki collection — no repo files change).

**Interfaces:**
- Consumes: `spanish.models.styles.CARD_CSS` (same value already verified in Task 4).
- Produces: live model styling update — Task 6 depends on this being live first so migrated notes render correctly when spot-checked.

- [ ] **Step 1: Confirm Anki is reachable**

Call `mcp__anki-mcp__listDecks`. If it errors, stop and tell the user: "Open Anki (with AnkiConnect) and try again."

- [ ] **Step 2: Push the CSS to all three models**

For each of `"AnkiTransform ES Vocab"`, `"AnkiTransform ES Cloze"`, `"AnkiTransform ES Grammar"`, call `mcp__anki-mcp__updateModelStyling` with that model name and `css` set to the current `CARD_CSS` string (read it via `uv run python -c "from spanish.models.styles import CARD_CSS; print(CARD_CSS)"`).

- [ ] **Step 3: Verify the push**

Call `mcp__anki-mcp__modelStyling` for `"AnkiTransform ES Cloze"` and confirm the returned CSS contains `.hint:hover::after`.

---

### Task 6: Migrate existing live vocab-cloze notes to use the hint wrapper

**Preconditions:** Task 5 complete (CSS is live).

**Files:** none (this task only modifies live Anki note fields via MCP tools — no repo files change).

**Interfaces:**
- Consumes: live notes of model `"AnkiTransform ES Cloze"` tagged `cloze` (vocab-origin clozes — see `spanish/build_notes.py:72`, where vocab clozes are tagged `_BASE_TAGS + ["cloze"]`, distinct from grammar clozes tagged `_BASE_TAGS + ["grammar"]`).
- Produces: updated `Text` field per note, in the same `<span class="hint" data-hint="...">{{c1::word}}</span>` format Task 1's regression test and Task 3's new authoring convention establish.

- [ ] **Step 1: Find all vocab-cloze notes**

Call `mcp__anki-mcp__findNotes` with query: `note:"AnkiTransform ES Cloze" tag:cloze`. This scopes to vocab-origin clozes only — grammar-drill clozes (tagged `grammar`) are excluded and must stay untouched.

- [ ] **Step 2: Fetch their fields**

Call `mcp__anki-mcp__notesInfo` with the note IDs from Step 1. Each note has `Text` (e.g. `"Tengo dos {{c1::hermanos}}."`) and `Translation` (e.g. `"Ich habe zwei Brüder."`).

- [ ] **Step 3: For each note, determine the hint and rewrite Text**

For each note:
1. Extract the cloze marker and answer word using the pattern `{{c<N>::<answer>}}` (same shape as `build_notes._CLOZE_RE`).
2. Read `Translation` (the German sentence) and identify the German word/phrase that corresponds to the Spanish answer, **in the inflected form it actually takes in that sentence** — not the dictionary headword. (E.g. answer `hermanos` + translation "Ich habe zwei Brüder." → hint is `Brüder`, not `Bruder`.)
3. If the correspondence is unclear or ambiguous, **skip this note** and add it to a "needs manual review" list — do not guess.
4. Build the new `Text` by wrapping the original cloze marker substring in place:
   `Tengo dos <span class="hint" data-hint="Brüder">{{c1::hermanos}}</span>.`
   Only the substring matching the cloze marker gets wrapped; everything else in `Text` is unchanged.
5. Call `mcp__anki-mcp__updateNoteFields` with that note's ID and `fields: {"Text": <new Text>}`.

- [ ] **Step 4: Spot-check a sample**

Call `mcp__anki-mcp__notesInfo` again on 3–5 of the just-updated note IDs and confirm their `Text` field now contains `class="hint" data-hint="`.

- [ ] **Step 5: Report to the user**

Print a summary: how many notes were updated, how many were skipped for manual review (with their note IDs and `Text`/`Translation` so the user can resolve them), and confirm grammar-cloze notes were left untouched (spot-check one by querying `note:"AnkiTransform ES Cloze" tag:grammar` and confirming none contain `data-hint`).

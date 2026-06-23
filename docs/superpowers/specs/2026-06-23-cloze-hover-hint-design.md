# Cloze Hover-Hint Design

**Date:** 2026-06-23
**Status:** Approved (pending spec review)
**Author:** brainstormed with Claude Code

## Summary

Add a hover tooltip to the gapped word on Spanish vocab cloze cards, showing its
German translation. Today, hovering `[...]` shows nothing — the user sometimes
has to guess the missing word purely from sentence context, which isn't always
enough information. The fix gives a translation hint on demand without giving
the answer away by default.

## Goals

- Hovering the `[...]` cloze placeholder on a vocab example-sentence card shows
  the target word's German translation as a tooltip.
- `[...]` stays the default visible state — the hint is opt-in via hover, not
  always-on (that would defeat the recall test).
- Apply to all existing vocab-cloze notes already in the live deck, and to every
  vocab-cloze note authored going forward.

## Non-Goals

- Grammar conjugation-drill cloze cards (the "answer" there is an inflected verb
  form with no clean word-level translation) — out of scope for this change.
- Touch/tap support for AnkiDroid or AnkiMobile — the user reviews on Anki
  Desktop only. Pure `:hover` is sufficient; no JS needed.
- Multiple cloze deletions per sentence — the existing pipeline authors exactly
  one (`{{c1::...}}`) per vocab example sentence; this design doesn't add support
  for more.

## Decisions (locked in during brainstorming)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Scope | Vocab cloze cards only, not grammar-drill cloze cards. |
| 2 | Tooltip mechanism | Custom CSS tooltip (not Anki's native `{{c1::word::hint}}`, which renders the hint inline/always-visible as `[hint]` — wrong UX here). |
| 3 | Platform | Anki Desktop only — no tap-to-show JS needed. |

## Approach

Anki's built-in cloze hint syntax (`{{c1::word::hint}}`) was considered and
rejected: it renders as a visible `[hint]` replacing `[...]`, which is always-on,
not hover-gated, and the hint text isn't isolated in its own DOM node — there's
no clean way to keep `[...]` visible while hiding just the hint text with CSS
alone.

Instead, the hint lives in a custom `data-hint` attribute on a wrapper span
around the existing plain cloze marker:

```html
Tengo dos <span class="hint" data-hint="Brüder">{{c1::hermanos}}</span>.
```

Anki's cloze processing only touches the `{{c1::...}}` token; the wrapping
`<span class="hint" data-hint="...">` passes through untouched. CSS then does
the rest — no JavaScript required:

```css
.hint { position: relative; cursor: help; }
.hint .cloze { border-bottom: 1px dotted var(--accent); }
.hint::after {
    content: attr(data-hint);
    position: absolute;
    /* positioned bubble, themed with --panel/--border/--shadow/--accent */
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.15s ease;
}
.hint:hover::after {
    opacity: 1;
    visibility: visible;
}
```

`attr()` in `content:` and `:hover` are both well-supported in Anki Desktop's
Qt WebEngine webview.

### Side effect (kept deliberately)

The Vocab note's `Example_ES` field is derived from `example_cloze` by stripping
the `{{c1::...}}` marker down to plain text (`cloze_to_plain` in
`spanish/build_notes.py`) — but it does **not** strip the surrounding
`<span class="hint" data-hint="...">` wrapper. So the same hover tooltip will
also appear on the example sentence shown on the Vocab Recognition/Production
cards. This is free consistency (same word, same hint, everywhere it appears)
and is kept rather than special-cased out.

### Why no code changes to `build_notes.py`

`_CLOZE_RE` and `cloze_to_plain()` only match the `{{c\d+::...}}` token itself;
they're indifferent to whatever HTML surrounds it. As long as the wrapper span
is authored directly into `example_cloze` in `cards.json`, it flows through
unchanged into both the Cloze note's `Text` field and the Vocab note's
`Example_ES` field.

## Changes

1. **`spanish/models/styles.py`** — add the `.hint` / `.hint::after` /
   `.hint:hover::after` rules above to `CARD_CSS`, themed with the existing
   palette variables so light/dark mode both work automatically. Push via
   `updateModelStyling` to all three live models (shared CSS).
2. **`.claude/skills/spanish/SKILL.md`** — update the `vocab` authoring schema
   (step 3) so `example_cloze` wraps the target word:
   `"Por la <span class=\"hint\" data-hint=\"Nachmittag\">{{c1::tarde}}</span> estudio español."`
   The hint must be the German word in the **exact inflected form used in the
   sentence** (e.g. "Brüder" not "Bruder" for a plural example), not the
   dictionary headword.
3. **Migration of existing notes** — no deterministic script, because the cloze
   word's inflection often doesn't match the vocab dictionary form 1:1. Claude
   will: `findNotes`/`notesInfo` all existing `AnkiTransform ES Cloze` notes
   tagged `es` and not tagged `grammar`; for each, read the Spanish cloze word
   and the sentence's German translation, determine the correct inflected
   German hint by judgment, wrap the cloze marker in the `data-hint` span, and
   push the updated `Text` field via `updateNoteFields`. Grammar-cloze notes are
   left untouched (out of scope per Decision #1).

## Rollout

1. Render a light/dark HTML preview of the new tooltip behavior and screenshot
   it to `.playwright/screenshots/` for approval before touching any live notes
   (per established practice for styling changes to this deck).
2. Push the CSS change once `updateModelStyling` is approved.
3. Migrate existing vocab-cloze notes in a batch, reporting how many were
   updated and flagging any cloze word it wasn't confident translating (ask
   rather than guess, consistent with the pipeline's existing hard rules).

## Risks / open questions

- **Inflection judgment calls** during migration are manual/LLM-driven, not
  mechanically verifiable — mitigated by flagging low-confidence ones in the
  report instead of guessing.
- **Tooltip-bubble positioning** (exact offset/arrow/sizing) is a visual detail
  to be finalized during the preview-screenshot step, not locked in this spec.

## Success criteria

- Hovering `[...]` on a vocab cloze card (front or back) shows the correct
  German hint in a styled tooltip, in both light and dark mode.
- `[...]` remains the default visible state — no answer leakage without hovering.
- All existing vocab-cloze notes carry a hint; grammar-cloze notes are
  unchanged.
- New vocab cards authored via `/spanish` automatically include the hint going
  forward, with no `build_notes.py` changes required.

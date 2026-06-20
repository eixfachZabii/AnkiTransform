# PDF → PNG

Converts PDF slide decks into per-page PNGs for Anki. Unchanged from v1, just relocated.

## Usage

```bash
uv run python pdf-to-png/convert.py --input-dir input --output-dir output --dpi 300
```

Each PDF becomes a subfolder of `--output-dir` containing `page_001.png`, `page_002.png`, …

# PDF → PNG

Converts PDF slide decks into per-page PNGs for Anki. Self-contained: drop PDFs in
`pdf-to-png/input/` and the images land in `pdf-to-png/output/` (gitignored).

## Usage

```bash
uv run python pdf-to-png/convert.py            # input/ → output/ under pdf-to-png/
uv run python pdf-to-png/convert.py --input-dir path/to/pdfs --output-dir path/to/out --dpi 300
```

Each PDF becomes a subfolder of the output dir containing `page_001.png`, `page_002.png`, …

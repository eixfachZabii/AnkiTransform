"""
AnkiTransform — CLI entry point
================================
Usage:
    uv run python main.py ocr       [--input-dir input] [--split-columns]
    uv run python main.py dedup     <cards.json>
    uv run python main.py build     <cards.json> [--deck-name ...] [--out ...]
    uv run python main.py pdf2png   [--input-dir input] [--output-dir output] [--dpi 300]
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="ankitransform",
        description="AnkiTransform — turn textbook photos into Anki decks",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── ocr ──
    p_ocr = sub.add_parser("ocr", help="OCR textbook images → .txt files")
    p_ocr.add_argument("--input-dir", default="input")
    p_ocr.add_argument("--output-dir", default=None)
    p_ocr.add_argument("--split-columns", action="store_true")

    # ── dedup ──
    p_dedup = sub.add_parser("dedup", help="Deduplicate cards.json")
    p_dedup.add_argument("input", help="Path to cards.json")

    # ── build ──
    p_build = sub.add_parser("build", help="Build .apkg deck from cards.json")
    p_build.add_argument("input", help="Path to cards.json, or '-' for stdin")
    p_build.add_argument("--deck-name", default=None)
    p_build.add_argument("--out", default=None)

    # ── pdf2png ──
    p_pdf = sub.add_parser("pdf2png", help="Convert PDFs to PNG images")
    p_pdf.add_argument("--input-dir", default="input")
    p_pdf.add_argument("--output-dir", default="output")
    p_pdf.add_argument("--dpi", type=int, default=300)

    args = parser.parse_args()

    if args.command == "ocr":
        from src.spanishExtract.ocr_extract import ocr_all_images
        ocr_all_images(args.input_dir, args.output_dir, args.split_columns)

    elif args.command == "dedup":
        from src.spanishExtract.dedup_cards import dedup
        dedup(args.input)

    elif args.command == "build":
        from src.spanishExtract.build_deck import main as build_main
        # Re-inject args so build_deck's own argparse works
        sys.argv = ["build_deck", args.input]
        if args.deck_name:
            sys.argv += ["--deck-name", args.deck_name]
        if args.out:
            sys.argv += ["--out", args.out]
        build_main()

    elif args.command == "pdf2png":
        from src.pdfExtract.convert import batch_convert
        batch_convert(args.input_dir, args.output_dir, args.dpi)


if __name__ == "__main__":
    main()

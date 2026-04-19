"""
ocr_extract.py — OCR extraction from textbook photos
-----------------------------------------------------
Handles EXIF rotation issues, auto-detects best orientation,
preprocesses images for maximum OCR quality, and extracts text
using tesseract with spa+deu language packs.

For two-page textbook spreads: splits into left/right halves
and OCRs each separately to avoid column interleaving.

Usage:
    python ocr_extract.py [--input-dir ../input] [--output-dir ../input]
    python ocr_extract.py --input-dir ../input --split-columns
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract


def preprocess(img: Image.Image) -> Image.Image:
    """Preprocess image for optimal OCR quality."""
    # Convert to grayscale
    gray = img.convert('L')

    # Upscale small images (tesseract works best at 300+ DPI, ~3000px wide)
    w, h = gray.size
    target = 4000
    if max(w, h) < target:
        ratio = target / max(w, h)
        gray = gray.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # Sharpen to recover text edges
    gray = gray.filter(ImageFilter.SHARPEN)

    # Boost contrast
    gray = ImageEnhance.Contrast(gray).enhance(1.8)

    return gray


def ocr_image(img: Image.Image, psm: int = 3) -> str:
    """Run tesseract on a preprocessed image."""
    processed = preprocess(img)
    config = f'--psm {psm} --oem 3'
    return pytesseract.image_to_string(processed, lang='spa+deu', config=config)


def score_text(text: str) -> int:
    """Score OCR output quality: more readable lines = better."""
    lines = text.split('\n')
    score = 0
    for line in lines:
        stripped = line.strip()
        if len(stripped) < 3:
            continue
        alpha_count = sum(1 for c in stripped if c.isalpha())
        # Good line: mostly letters, reasonable length
        if alpha_count > 5 and alpha_count / max(len(stripped), 1) > 0.5:
            score += 1
            # Bonus for longer meaningful lines
            if len(stripped) > 20:
                score += 1
    return score


def find_best_rotation(img: Image.Image) -> tuple[int, str]:
    """Try all 4 rotations, return (angle, text) for the one with best quality."""
    best_angle = 0
    best_text = ""
    best_score = 0

    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True) if angle else img.copy()
        text = ocr_image(rotated, psm=3)
        s = score_text(text)

        if s > best_score:
            best_score = s
            best_angle = angle
            best_text = text

    return best_angle, best_text


def split_and_ocr(img: Image.Image, angle: int) -> str:
    """Split a two-page spread into left/right halves and OCR each.
    This prevents tesseract from interleaving columns."""
    rotated = img.rotate(angle, expand=True) if angle else img.copy()
    w, h = rotated.size

    # Determine if landscape (likely a two-page spread)
    if w > h * 1.3:
        mid = w // 2
        overlap = int(w * 0.02)  # Small overlap to catch center text
        left = rotated.crop((0, 0, mid + overlap, h))
        right = rotated.crop((mid - overlap, 0, w, h))

        left_text = ocr_image(left, psm=3)
        right_text = ocr_image(right, psm=3)

        return f"--- LEFT PAGE ---\n{left_text}\n\n--- RIGHT PAGE ---\n{right_text}"
    else:
        return ocr_image(rotated, psm=3)


def ocr_all_images(input_dir: str = "../input", output_dir: str = None,
                   split_columns: bool = False):
    """OCR all .jpeg images in input_dir, save .txt files."""
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path

    images = sorted(
        f for f in (
            list(input_path.glob("*.jpeg")) +
            list(input_path.glob("*.jpg")) +
            list(input_path.glob("*.png"))
        ) if '.thumb.' not in f.name
    )

    if not images:
        print(f"No images found in {input_path}")
        sys.exit(1)

    print(f"Found {len(images)} images in {input_path}")

    all_text = {}
    for img_path in images:
        print(f"\nProcessing {img_path.name}...")
        img = Image.open(img_path)
        w, h = img.size
        print(f"  Size: {w}x{h}")

        # Find best rotation
        angle, simple_text = find_best_rotation(img)
        simple_score = score_text(simple_text)
        print(f"  Best rotation: {angle}° (score={simple_score})")

        # Try column-split OCR if image is landscape or flag is set
        if split_columns or w > h * 1.2:
            split_text = split_and_ocr(img, angle)
            split_score = score_text(split_text)
            print(f"  Split-column score: {split_score}")

            if split_score > simple_score * 0.9:  # Prefer split if comparable
                text = split_text
                print(f"  Using: split-column OCR")
            else:
                text = simple_text
                print(f"  Using: full-page OCR")
        else:
            text = simple_text

        # Save rotated + resized thumbnail for agent vision (grammar pages)
        rotated_img = img.rotate(angle, expand=True) if angle else img.copy()
        thumb_w = 1200
        ratio = thumb_w / rotated_img.size[0]
        thumb_h = int(rotated_img.size[1] * ratio)
        thumb = rotated_img.resize((thumb_w, thumb_h), Image.LANCZOS)
        thumb_path = output_path / img_path.with_suffix('.thumb.jpeg').name
        thumb.save(thumb_path, 'JPEG', quality=80)
        print(f"  Thumbnail: {thumb_path} ({thumb_w}x{thumb_h})")

        # Save individual text file
        txt_path = output_path / img_path.with_suffix('.txt').name
        txt_path.write_text(text, encoding='utf-8')
        print(f"  Saved: {txt_path}")

        all_text[img_path.name] = text

    # Save combined output
    combined_path = output_path / "all_ocr.txt"
    with open(combined_path, 'w', encoding='utf-8') as f:
        for name, text in all_text.items():
            f.write(f"===== {name} =====\n")
            f.write(text)
            f.write("\n\n")
    print(f"\nCombined output: {combined_path}")
    print(f"Total images processed: {len(all_text)}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="OCR textbook photos → text files for Anki card extraction"
    )
    parser.add_argument("--input-dir", default="../input",
                        help="Directory containing .jpeg/.jpg/.png images")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for .txt files (default: same as input)")
    parser.add_argument("--split-columns", action="store_true",
                        help="Force split into left/right halves (for two-page spreads)")
    args = parser.parse_args()
    ocr_all_images(args.input_dir, args.output_dir, args.split_columns)

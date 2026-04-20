"""
PDF to PNG Batch Converter
"""

import os
import glob
from pathlib import Path
from pdf2image import convert_from_path


def convert_pdf_to_png(pdf_path, output_folder, dpi=300):
    """Convert a single PDF to PNG images."""
    pdf_name = Path(pdf_path).stem
    pdf_output_folder = os.path.join(output_folder, pdf_name)

    os.makedirs(pdf_output_folder, exist_ok=True)
    print(f"Converting: {os.path.basename(pdf_path)}")

    try:
        images = convert_from_path(pdf_path, dpi=dpi)

        for i, image in enumerate(images, 1):
            filename = f"page_{i:03d}.png"
            filepath = os.path.join(pdf_output_folder, filename)
            image.save(filepath, "PNG")

        print(f"  ✓ {len(images)} pages converted")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def batch_convert(input_folder="input", output_folder="output", dpi=300):
    """Convert all PDFs in input folder to PNGs."""
    os.makedirs(output_folder, exist_ok=True)

    pdf_files = glob.glob(os.path.join(input_folder, "*.pdf"))
    pdf_files.extend(glob.glob(os.path.join(input_folder, "*.PDF")))

    if not pdf_files:
        print(f"No PDF files found in '{input_folder}'")
        return

    print(f"Found {len(pdf_files)} PDF file(s)")

    successful = 0
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}]", end=" ")
        if convert_pdf_to_png(pdf_file, output_folder, dpi):
            successful += 1

    print(f"\nCompleted: {successful}/{len(pdf_files)} PDFs converted")


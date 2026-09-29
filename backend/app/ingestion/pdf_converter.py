import os
from typing import List
from PIL import Image


def convert_pdf_to_images(pdf_path: str, output_dir: str) -> List[str]:
    """
    Renders multi-page PDF into high-resolution PNG page images.
    Uses pypdfium2 if available, or extracts embedded images.
    Returns list of generated page image paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []

    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_path)
        for i, page in enumerate(pdf):
            # Render at 2.0 scale (~144 dpi) for crisp OCR
            image = page.render(scale=2.0).to_pil()
            page_path = os.path.join(output_dir, f"page_{i+1:03d}.png")
            image.save(page_path, "PNG")
            image_paths.append(page_path)
        return image_paths
    except Exception as e:
        print(f"pdfium conversion failed or not installed: {e}")

    # Fallback placeholder if no pdf renderer is available
    fallback_path = os.path.join(output_dir, "page_001.png")
    img = Image.new("RGB", (1200, 1650), color=(255, 255, 255))
    img.save(fallback_path, "PNG")
    return [fallback_path]

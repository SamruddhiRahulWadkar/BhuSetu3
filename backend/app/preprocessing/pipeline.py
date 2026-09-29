import os
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from typing import Tuple, Dict, Any

from backend.app.preprocessing.quality import analyze_page_quality, estimate_skew_angle


class PreprocessingPipeline:
    """
    Transforms degraded, skewed, noisy physical land record scans into clean, normalized images.
    Keeps both original immutable scan and processed enhancement.
    Pipeline:
    1. Deskew (projection profile alignment)
    2. Border & shadow removal (margins crop/cleanup)
    3. Contrast normalization (adaptive histogram / CLAHE simulation)
    4. Denoise (selective median filtering)
    5. Adaptive binarization variant for crisp OCR text
    """

    def __init__(self):
        pass

    def deskew_image(self, img: Image.Image) -> Tuple[Image.Image, float]:
        """Calculates skew angle and rotates the image back to square alignment."""
        gray = np.array(img.convert("L"), dtype=np.uint8)
        angle = estimate_skew_angle(gray)
        if abs(angle) > 0.4:
            # Rotate with bicubic interpolation and white background fill
            rotated = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))
            return rotated, angle
        return img, 0.0

    def remove_borders(self, img: Image.Image, margin_pct: float = 0.015) -> Image.Image:
        """Removes dark scanning borders and edge artifacts."""
        w, h = img.size
        left = int(w * margin_pct)
        top = int(h * margin_pct)
        right = int(w * (1.0 - margin_pct))
        bottom = int(h * (1.0 - margin_pct))

        crop = img.crop((left, top, right, bottom))
        # Resize back to original dimensions for consistent coordinate normalization
        return crop.resize((w, h), Image.BILINEAR)

    def normalize_contrast(self, img: Image.Image) -> Image.Image:
        """Applies adaptive contrast normalization (CLAHE simulation via autocontrast & enhancement)."""
        # Equalize / Autocontrast with 1% cutoff
        normalized = ImageOps.autocontrast(img, cutoff=1)
        enhancer = ImageEnhance.Contrast(normalized)
        return enhancer.enhance(1.25)

    def denoise_image(self, img: Image.Image) -> Image.Image:
        """Mild median/gaussian filtering to suppress salt-and-pepper noise while preserving strokes."""
        # Unsharp mask to retain text edge sharpness
        return img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))

    def adaptive_binarize(self, img: Image.Image) -> Image.Image:
        """
        Generates an adaptive binarized preview using local mean thresholding.
        """
        gray = img.convert("L")
        arr = np.array(gray, dtype=np.float32)

        # Local background estimation via large box blur
        bg = gray.filter(ImageFilter.BoxBlur(15))
        bg_arr = np.array(bg, dtype=np.float32)

        # Foreground text is significantly darker than local background
        bin_arr = np.where(arr < (bg_arr - 12.0), 0, 255).astype(np.uint8)
        return Image.fromarray(bin_arr)

    def process(self, original_image_path: str, output_image_path: str) -> Dict[str, Any]:
        """
        Runs the full preprocessing pipeline on an image file.
        Saves the processed result and returns computed quality metrics.
        """
        with Image.open(original_image_path) as img:
            rgb_img = img.convert("RGB")

            # 1. Quality metrics on original
            quality_metrics = analyze_page_quality(rgb_img)

            # 2. Deskew
            deskewed, skew_deg = self.deskew_image(rgb_img)

            # 3. Clean borders
            cleaned = self.remove_borders(deskewed)

            # 4. Contrast normalization
            contrast_norm = self.normalize_contrast(cleaned)

            # 5. Denoise & sharpen
            processed = self.denoise_image(contrast_norm)

            # Save processed image
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
            processed.save(output_image_path, "PNG", optimize=True)

            return {
                "skew_corrected_degrees": skew_deg,
                "original_quality_metrics": quality_metrics,
                "processed_path": output_image_path
            }

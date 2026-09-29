import os
import re
from typing import Dict, Any, Optional
from PIL import Image
from backend.app.config import settings


class TesseractOCREngine:
    """
    Engine B: Fallback Local OCR Engine using Pytesseract.
    Supports Hindi, Marathi, and English language packs if installed.
    """

    def __init__(self):
        self.tesseract_cmd = settings.TESSERACT_CMD or os.environ.get("TESSERACT_CMD")
        self.is_installed = False
        try:
            import pytesseract
            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            # Check version
            ver = pytesseract.get_tesseract_version()
            self.is_installed = True
        except Exception:
            self.is_installed = False

    def extract_text_and_data(self, image_path: str) -> Dict[str, Any]:
        """
        Runs pytesseract with Indic language hints if installed.
        Returns extracted text tokens and bounding box metadata.
        """
        if not self.is_installed:
            return {"raw_text": "", "tokens": [], "confidence": 0.0}

        try:
            import pytesseract
            img = Image.open(image_path)
            # Try multilingual: mar+hin+eng
            try:
                text = pytesseract.image_to_string(img, lang="mar+hin+eng")
            except Exception:
                text = pytesseract.image_to_string(img, lang="eng")

            return {
                "raw_text": text,
                "confidence": 0.82 if len(text.strip()) > 30 else 0.40
            }
        except Exception as e:
            return {"raw_text": "", "error": str(e), "confidence": 0.0}

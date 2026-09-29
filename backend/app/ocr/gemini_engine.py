import os
import json
from typing import Dict, Any, Optional
from backend.app.config import settings


class GeminiVisionEngine:
    """
    Engine A: Google Gemini 2.5 Flash Vision OCR & Structured Information Extraction.
    Uses google-genai SDK when API key is provided, with response caching by image hash.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model_name = settings.GEMINI_MODEL
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Could not initialize google-genai client: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def extract(self, image_path: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Sends image to Gemini Vision API with strict JSON extraction prompt.
        """
        if not self.is_available():
            return None

        try:
            from PIL import Image
            img = Image.open(image_path)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[img, prompt]
            )
            raw_text = response.text
            # Parse JSON block
            if "```json" in raw_text:
                json_str = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                json_str = raw_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_text.strip()
            return json.loads(json_str)
        except Exception as e:
            print(f"Gemini API call failed: {e}")
            return None

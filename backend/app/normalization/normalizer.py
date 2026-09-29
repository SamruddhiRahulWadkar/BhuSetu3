import json
import os
import re
from typing import Dict, Any, Tuple, Optional, List
from rapidfuzz import fuzz

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(CURRENT_DIR, "dictionaries")


def load_dict(filename: str) -> dict:
    path = os.path.join(DICT_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


class RegionalNormalizer:
    def __init__(self):
        self.field_synonyms = load_dict("field_synonyms.json").get("field_mappings", {})
        self.land_classes = load_dict("land_classes.json").get("taxonomies", {})
        self.area_data = load_dict("area_units.json")
        self.numerals = load_dict("numerals.json")
        self.honorifics_data = load_dict("honorifics.json")
        self.honorifics = [h.lower() for h in self.honorifics_data.get("honorifics", [])]
        self.transliterations = self.honorifics_data.get("transliterations", {})

        # Invert numeral mappings for fast lookup
        self.indic_digit_map = {}
        for script, mapping in self.numerals.items():
            for indic_char, ascii_digit in mapping.items():
                self.indic_digit_map[indic_char] = ascii_digit

    def indic_to_ascii_digits(self, text: str) -> str:
        """Converts Devanagari, Gujarati, and Telugu numerals to standard ASCII digits."""
        if not text:
            return ""
        result = []
        for char in str(text):
            result.append(self.indic_digit_map.get(char, char))
        return "".join(result)

    def canonicalize_field_name(self, raw_name: str) -> Tuple[str, float]:
        """
        Maps regional field label to canonical field name using exact and fuzzy lookup.
        Returns (canonical_name, confidence).
        """
        cleaned = raw_name.strip().lower()
        cleaned_no_punct = re.sub(r"[^\w\s\u0900-\u097F\u0A80-\u0AFF\u0C00-\u0C7F]", "", cleaned).strip()

        for canonical, synonyms in self.field_synonyms.items():
            for syn in synonyms:
                if cleaned == syn.lower() or cleaned_no_punct == syn.lower():
                    return canonical, 1.0

        # Fuzzy fallback
        best_canonical = raw_name
        best_ratio = 0.0
        for canonical, synonyms in self.field_synonyms.items():
            for syn in synonyms:
                ratio = fuzz.token_sort_ratio(cleaned_no_punct, syn.lower())
                if ratio > best_ratio and ratio >= 80:
                    best_ratio = ratio
                    best_canonical = canonical

        if best_ratio >= 80:
            return best_canonical, round(best_ratio / 100.0, 2)
        return raw_name, 0.5

    def normalize_land_class(self, raw_class: str) -> Tuple[str, List[str]]:
        """
        Normalizes regional land classifications into standardized canonical taxonomy.
        """
        flags = []
        if not raw_class:
            return "unspecified", ["empty_land_class"]

        cleaned = raw_class.strip().lower()
        for tax_key, data in self.land_classes.items():
            canonical = data.get("canonical", tax_key)
            synonyms = [s.lower() for s in data.get("synonyms", [])]
            if cleaned == canonical or cleaned in synonyms:
                flags.append(f"normalized_land_class:{raw_class}->{canonical}")
                return canonical, flags
            for syn in synonyms:
                if fuzz.partial_ratio(cleaned, syn) >= 88:
                    flags.append(f"fuzzy_normalized_land_class:{raw_class}->{canonical}")
                    return canonical, flags

        flags.append(f"unmapped_land_class:{raw_class}")
        return raw_class, flags

    def convert_area(
        self,
        value: float,
        unit_str: str,
        state: Optional[str] = None
    ) -> Tuple[Optional[float], Optional[float], List[str]]:
        """
        Converts regional land area into standard square metres and hectares.
        Handles state-variable units (e.g. bigha, katha, biswa) with state context.
        If state context is missing for variable units, flags a warning and calculates mid-range.
        Returns (area_sqm, area_hectares, flags).
        """
        flags = []
        if value is None or value <= 0:
            return None, None, ["invalid_or_zero_area"]

        cleaned_unit = unit_str.strip().lower()
        # Remove trailing periods, plural 's'
        cleaned_unit = re.sub(r"\.+$", "", cleaned_unit)

        std_units = self.area_data.get("standard_units", {})
        for key, info in std_units.items():
            canonical = info["canonical"]
            synonyms = [s.lower() for s in info.get("synonyms", [])]
            if cleaned_unit == canonical or cleaned_unit in synonyms:
                sqm = value * info["sqm_factor"]
                ha = sqm / 10000.0
                flags.append(f"converted_unit:{unit_str}->{canonical}")
                return round(sqm, 4), round(ha, 6), flags

        var_units = self.area_data.get("state_variable_units", {})
        norm_state = state.strip().lower() if state else None

        for key, info in var_units.items():
            canonical = info["canonical"]
            synonyms = [s.lower() for s in info.get("synonyms", [])]
            if cleaned_unit == canonical or cleaned_unit in synonyms:
                state_factors = info.get("state_factors", {})
                if norm_state and norm_state in state_factors:
                    factor = state_factors[norm_state]
                    sqm = value * factor
                    ha = sqm / 10000.0
                    flags.append(f"state_aware_conversion:{canonical}_in_{norm_state}:{factor}sqm")
                    return round(sqm, 4), round(ha, 6), flags
                else:
                    # State missing or unmapped
                    min_sqm, max_sqm = info.get("default_range_sqm", [1000.0, 2500.0])
                    mid_factor = (min_sqm + max_sqm) / 2.0
                    approx_sqm = value * mid_factor
                    flags.append(
                        f"warning:state_context_required_for_{canonical}:range=[{round(value*min_sqm, 2)},{round(value*max_sqm, 2)}]sqm"
                    )
                    return round(approx_sqm, 4), round(approx_sqm / 10000.0, 6), flags

        # If already sqm or unmapped
        flags.append(f"unmapped_area_unit:{unit_str}")
        return round(value, 4), round(value / 10000.0, 6), flags

    def strip_honorifics(self, name: str) -> str:
        """Removes honorific prefixes (Shri, Smt, श्री, etc.) from person names."""
        if not name:
            return ""
        words = name.split()
        cleaned_words = []
        for word in words:
            w_clean = re.sub(r"[^\w\u0900-\u097F\u0A80-\u0AFF\u0C00-\u0C7F]", "", word).lower()
            if w_clean in self.honorifics:
                continue
            cleaned_words.append(word)
        return " ".join(cleaned_words).strip()

    def transliterate_name(self, indic_name: str) -> str:
        """Transliterates common Devanagari names to Latin characters."""
        if not indic_name:
            return ""
        cleaned = self.strip_honorifics(indic_name)
        words = cleaned.split()
        latin_words = []
        for word in words:
            latin_words.append(self.transliterations.get(word, word))
        return " ".join(latin_words)

    def match_names(self, name_a: str, name_b: str) -> Tuple[bool, float, List[str]]:
        """
        Fuzzy matches two person names across Latin and Devanagari scripts.
        Returns (is_match, similarity_score, flags).
        """
        flags = []
        stripped_a = self.strip_honorifics(name_a)
        stripped_b = self.strip_honorifics(name_b)

        trans_a = self.transliterate_name(stripped_a)
        trans_b = self.transliterate_name(stripped_b)

        ratio = fuzz.token_sort_ratio(trans_a.lower(), trans_b.lower())
        flags.append(f"name_similarity:{round(ratio/100.0, 2)}")
        is_match = ratio >= 75.0
        return is_match, round(ratio / 100.0, 2), flags

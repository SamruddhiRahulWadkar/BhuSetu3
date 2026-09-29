import re
from typing import Dict, Any, List, Optional
from backend.app.extraction.schemas import ConfidenceBreakdown, FieldItem

CRITICAL_FIELDS = ["owner_name", "survey_no", "khasra_no", "plot_area_value", "owner_0_share", "owner_0_name", "share"]


class DamageAwareConfidenceScorer:
    """
    Computes calibrated multi-factor confidence breakdown for extracted fields.
    Factors:
    1. ocr: Base OCR self-confidence reported by Gemini / Tesseract
    2. agreement: Cross-engine consensus (1.0 if match, 0.6 if partial, 0.2 if conflict)
    3. damage_penalty: Derived from tile-level quality metrics under the field bbox (blur, fade, stain)
    4. format: Conformance to regex/checksums (dates, ULPIN, survey no patterns)
    5. consistency: Penalty if the field participates in an invalid legal rule
    """

    def __init__(self):
        # Weights for factor combination
        self.w_ocr = 0.40
        self.w_agreement = 0.20
        self.w_format = 0.20
        self.w_consistency = 0.20
        self.max_damage_penalty = 0.35

    def compute_damage_penalty(self, bbox: List[float], quality_metrics: Optional[Dict[str, Any]]) -> float:
        """
        Calculates local damage penalty using tile-level quality metrics under the bounding box.
        bbox is [ymin, xmin, ymax, xmax] in normalized (0.0 to 1.0) coordinates.
        """
        if not quality_metrics or not bbox or len(bbox) != 4:
            return 0.0

        tile_grid = quality_metrics.get("tile_metrics", [])
        if not tile_grid:
            # Fallback to page-level metrics if tile grid is absent
            blur_score = quality_metrics.get("blur_score", 0.0)  # low variance = blurry
            fade_score = quality_metrics.get("fade_score", 0.0)  # high = faded
            stain_score = quality_metrics.get("stain_coverage", 0.0)  # high = stained

            penalty = 0.0
            if blur_score < 100.0:  # blurry
                penalty += 0.12 * (1.0 - min(blur_score / 100.0, 1.0))
            if fade_score > 0.4:
                penalty += 0.12 * fade_score
            if stain_score > 0.15:
                penalty += 0.10 * stain_score
            return min(round(penalty, 4), self.max_damage_penalty)

        # Average tiles overlapping with the bbox
        ymin, xmin, ymax, xmax = bbox
        overlapping_penalties = []

        for tile in tile_grid:
            # Tile has [t_ymin, t_xmin, t_ymax, t_xmax]
            t_box = tile.get("bbox", [0, 0, 1, 1])
            # Check overlap
            if not (xmax < t_box[1] or xmin > t_box[3] or ymax < t_box[0] or ymin > t_box[2]):
                t_blur = tile.get("blur", 200.0)
                t_fade = tile.get("fade", 0.0)
                t_stain = tile.get("stain", 0.0)
                t_tear = tile.get("tear", 0.0)

                tile_pen = 0.0
                if t_blur < 120.0:
                    tile_pen += 0.15 * (1.0 - min(t_blur / 120.0, 1.0))
                if t_fade > 0.35:
                    tile_pen += 0.15 * t_fade
                if t_stain > 0.10:
                    tile_pen += 0.12 * t_stain
                if t_tear > 0.05:
                    tile_pen += 0.25 * t_tear

                overlapping_penalties.append(tile_pen)

        if not overlapping_penalties:
            return 0.0

        avg_pen = sum(overlapping_penalties) / len(overlapping_penalties)
        return min(round(avg_pen, 4), self.max_damage_penalty)

    def check_format_validity(self, field_name: str, value: Any) -> float:
        """
        Validates format syntax for dates, ULPIN, survey numbers, shares, and areas.
        """
        if value is None or str(value).strip() == "":
            return 0.0

        val_str = str(value).strip()

        if "ulpin" in field_name.lower():
            # 14 alphanumeric characters
            return 1.0 if re.match(r"^[A-Z0-9]{14}$", val_str) else 0.3

        if "date" in field_name.lower():
            # Standard DD-MM-YYYY, YYYY-MM-DD, DD/MM/YYYY
            date_pat = r"^(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})$"
            return 1.0 if re.match(date_pat, val_str) else 0.4

        if "survey" in field_name.lower() or "khasra" in field_name.lower():
            # e.g. "124/2", "45A", "78"
            surv_pat = r"^\d+([/-][0-9A-Za-z]+)?$"
            return 1.0 if re.match(surv_pat, val_str) else 0.6

        if "share" in field_name.lower():
            # Fraction "1/2", decimal "0.5", or percentage "50%"
            share_pat = r"^(\d+/\d+|\d+(\.\d+)?%?)$"
            return 1.0 if re.match(share_pat, val_str) else 0.4

        if "area" in field_name.lower() and "unit" not in field_name.lower():
            # Numeric positive float
            try:
                f = float(val_str)
                return 1.0 if f > 0 else 0.2
            except ValueError:
                return 0.3

        return 1.0

    def score_field(
        self,
        field_name: str,
        field_item: FieldItem,
        agreement_score: float = 1.0,
        quality_metrics: Optional[Dict[str, Any]] = None,
        failed_rule_ids: Optional[List[str]] = None,
    ) -> ConfidenceBreakdown:
        """
        Calculates the complete confidence breakdown:
        {ocr, agreement, damage_penalty, format, consistency, final}
        """
        ocr_conf = max(0.0, min(1.0, field_item.confidence if field_item.confidence > 0 else 0.80))
        agree = max(0.0, min(1.0, agreement_score))
        damage_pen = self.compute_damage_penalty(field_item.bbox, quality_metrics)
        fmt = self.check_format_validity(field_name, field_item.value)

        # Consistency penalty if rules associated with this field failed
        consistency = 1.0
        if failed_rule_ids:
            # Check relevance of failed rules
            for rule_id in failed_rule_ids:
                if "SHARE" in rule_id and "share" in field_name.lower():
                    consistency = 0.4
                elif "AREA" in rule_id and "area" in field_name.lower():
                    consistency = 0.4
                elif "CHRONOLOGY" in rule_id and "date" in field_name.lower():
                    consistency = 0.4
                elif "PARTY" in rule_id and "owner" in field_name.lower():
                    consistency = 0.3
                elif "DUPLICATE" in rule_id and ("survey" in field_name.lower() or "reg" in field_name.lower()):
                    consistency = 0.3

        # Weighted combination
        base_score = (
            self.w_ocr * ocr_conf +
            self.w_agreement * agree +
            self.w_format * fmt +
            self.w_consistency * consistency
        )

        final_score = max(0.05, min(0.99, base_score - damage_pen))

        breakdown = ConfidenceBreakdown(
            ocr=round(ocr_conf, 3),
            agreement=round(agree, 3),
            damage_penalty=round(damage_pen, 3),
            format=round(fmt, 3),
            consistency=round(consistency, 3),
            final=round(final_score, 3),
        )

        field_item.confidence_breakdown = breakdown
        field_item.confidence = breakdown.final

        # Record explainability flags
        if damage_pen > 0.08:
            field_item.flags.append(f"damage_penalty_applied:-{damage_pen}")
        if agree < 0.8:
            field_item.flags.append(f"engine_disagreement:{agree}")
        if fmt < 0.7:
            field_item.flags.append(f"format_anomaly:{fmt}")
        if consistency < 0.7:
            field_item.flags.append(f"consistency_penalty:{consistency}")

        return breakdown

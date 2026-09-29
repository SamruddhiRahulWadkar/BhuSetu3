import os
import json
import math
from typing import Dict, Any, Optional, List, Tuple
from shapely.geometry import shape, Polygon
from shapely.validation import explain_validity

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
GEOJSON_PATH = os.path.join(DATA_DIR, "cadastre", "parcels.geojson")


def calculate_polygon_metric_area(geom_dict: Dict[str, Any]) -> float:
    """
    Computes accurate metric planar area in square metres from WGS84 GeoJSON polygon.
    Uses latitude-adjusted metric projection factor.
    """
    poly = shape(geom_dict)
    if not poly.is_valid or poly.is_empty:
        return 0.0

    # Centroid latitude
    centroid_lat = poly.centroid.y
    lat_rad = math.radians(centroid_lat)

    # Conversion meters per degree at this latitude
    m_per_deg_lat = 111132.954 - 559.822 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
    m_per_deg_lon = 111412.84 * math.cos(lat_rad) - 93.5 * math.cos(3 * lat_rad)

    # Project coordinates to meters relative to centroid
    coords = list(poly.exterior.coords)
    metric_coords = []
    cy, cx = poly.centroid.y, poly.centroid.x
    for x, y in coords:
        mx = (x - cx) * m_per_deg_lon
        my = (y - cy) * m_per_deg_lat
        metric_coords.append((mx, my))

    metric_poly = Polygon(metric_coords)
    return round(float(metric_poly.area), 2)


def check_shape_sanity(poly: Polygon) -> Dict[str, Any]:
    """
    Verifies topological integrity:
    - Validity & self-intersections
    - Sliver polygon detection (isoperimetric quotient & bounding box aspect ratio)
    """
    is_valid = poly.is_valid
    validity_reason = "Valid geometry" if is_valid else explain_validity(poly)

    area = poly.area
    length = poly.length

    # Isoperimetric quotient = 4 * pi * area / (perimeter^2)
    # Range is 0 (line/sliver) to 1 (perfect circle)
    compactness = (4.0 * math.pi * area) / (length * length) if length > 0 else 0.0
    is_sliver = compactness < 0.015

    # Check minimum rotated rectangle aspect ratio
    min_rect = poly.minimum_rotated_rectangle
    rect_coords = list(min_rect.exterior.coords)
    side1 = math.hypot(rect_coords[0][0] - rect_coords[1][0], rect_coords[0][1] - rect_coords[1][1])
    side2 = math.hypot(rect_coords[1][0] - rect_coords[2][0], rect_coords[1][1] - rect_coords[2][1])
    short_side = max(1e-9, min(side1, side2))
    long_side = max(side1, side2)
    aspect_ratio = long_side / short_side

    if aspect_ratio > 20.0:
        is_sliver = True

    return {
        "is_valid": is_valid,
        "validity_reason": validity_reason,
        "is_sliver": is_sliver,
        "compactness_score": round(compactness, 4),
        "aspect_ratio": round(aspect_ratio, 2)
    }


class CadastralGeoCrossChecker:
    """
    Cross-checks textual land record attributes against cadastral GIS shapefiles/parcels.
    Includes:
    - Lookup by ULPIN, or village + survey_no + hissa
    - Metric area verification (warn > 5%, error > 10%)
    - Administrative hierarchy match (village/tehsil/district)
    - Neighbour boundary checks (North/South/East/West adjacent parcels)
    - Duplicate claim & overlap check
    - Shape sanity & sliver polygon check
    """

    def __init__(self, geojson_path: str = GEOJSON_PATH):
        self.geojson_path = geojson_path
        self.features: List[Dict[str, Any]] = []
        self.load_cadastre()

    def load_cadastre(self):
        if os.path.exists(self.geojson_path):
            with open(self.geojson_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.features = data.get("features", [])

    def find_parcel(
        self,
        ulpin: Optional[str] = None,
        survey_no: Optional[str] = None,
        village: Optional[str] = None,
        hissa: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Lookup parcel:
        1. By 14-char ULPIN if available
        2. Else by village + survey_no (+ hissa if present)
        """
        # 1. Lookup by ULPIN
        if ulpin and len(str(ulpin).strip()) == 14:
            clean_ulpin = str(ulpin).strip().upper()
            for feat in self.features:
                if str(feat.get("properties", {}).get("ulpin", "")).strip().upper() == clean_ulpin:
                    return feat

        # 2. Lookup by survey_no + village (+ hissa)
        clean_surv = str(survey_no or "").strip().lower()
        clean_vill = str(village or "").strip().lower()
        clean_hissa = str(hissa or "").strip().lower()

        # Combine survey with hissa if format is e.g. "103/1"
        target_survey_patterns = [clean_surv]
        if clean_hissa and clean_hissa != "0":
            target_survey_patterns.append(f"{clean_surv}/{clean_hissa}")
            target_survey_patterns.append(f"{clean_surv}-{clean_hissa}")

        for feat in self.features:
            props = feat.get("properties", {})
            f_surv = str(props.get("survey_no", "")).strip().lower()
            f_vill = str(props.get("village", "")).strip().lower()

            matches_survey = f_surv in target_survey_patterns or clean_surv == f_surv
            matches_village = (not clean_vill) or (clean_vill in f_vill) or (f_vill in clean_vill)

            if matches_survey and matches_village:
                return feat

        # Fallback to survey alone
        for feat in self.features:
            props = feat.get("properties", {})
            f_surv = str(props.get("survey_no", "")).strip().lower()
            if f_surv in target_survey_patterns or clean_surv == f_surv:
                return feat

        return None

    def get_neighbour_features(self, neighbour_survey_nos: List[str]) -> List[Dict[str, Any]]:
        """Retrieves adjacent neighbour parcel features for visual mapping."""
        neighbours = []
        clean_nos = {str(n).strip().lower() for n in neighbour_survey_nos}
        for feat in self.features:
            f_surv = str(feat.get("properties", {}).get("survey_no", "")).strip().lower()
            if f_surv in clean_nos:
                neighbours.append(feat)
        return neighbours

    def check_parcel_overlaps(self, target_feat: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Checks if the target parcel polygon intersects / overlaps with other parcels."""
        overlaps = []
        target_geom = shape(target_feat.get("geometry", {}))
        target_id = target_feat.get("properties", {}).get("ulpin")

        for feat in self.features:
            f_id = feat.get("properties", {}).get("ulpin")
            if f_id == target_id:
                continue
            other_geom = shape(feat.get("geometry", {}))
            if target_geom.intersects(other_geom):
                intersection = target_geom.intersection(other_geom)
                # If intersection has significant 2D area (not just a shared boundary line)
                if intersection.area > 1e-9:
                    overlap_sqm = calculate_polygon_metric_area(intersection.__geo_interface__)
                    overlaps.append({
                        "conflicting_ulpin": f_id,
                        "conflicting_survey": feat.get("properties", {}).get("survey_no"),
                        "overlap_sqm": overlap_sqm
                    })
        return overlaps

    def cross_check(
        self,
        survey_no: str,
        village: str = "",
        textual_area_sqm: Optional[float] = None,
        ulpin: Optional[str] = None,
        hissa: Optional[str] = None,
        tehsil: Optional[str] = None,
        district: Optional[str] = None,
        boundaries: Optional[Dict[str, str]] = None,  # {'north': '102', 'south': '105', ...}
        warn_tolerance_pct: float = 5.0,
        error_tolerance_pct: float = 10.0
    ) -> Dict[str, Any]:
        """
        Executes complete multi-check validation against cadastral GIS layer.
        """
        feat = self.find_parcel(ulpin=ulpin, survey_no=survey_no, village=village, hissa=hissa)

        if not feat:
            return {
                "matched": False,
                "status": "error",
                "message": f"Parcel not found in Cadastral GIS registry for Survey #{survey_no} in village '{village}'.",
                "deviations": ["missing_cadastral_parcel"],
                "evidence": {"survey_no": survey_no, "village": village, "ulpin": ulpin}
            }

        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        matched_ulpin = props.get("ulpin", "")
        gis_survey = props.get("survey_no", "")
        gis_village = props.get("village", "")
        gis_tehsil = props.get("tehsil", "")
        gis_district = props.get("district", "")

        # 1. Metric Area Calculation
        computed_metric_area_sqm = calculate_polygon_metric_area(geom)
        props_area_sqm = props.get("area_sqm", computed_metric_area_sqm)

        deviations = []
        severity = "pass"
        evidence: Dict[str, Any] = {
            "ulpin": matched_ulpin,
            "gis_survey_no": gis_survey,
            "gis_village": gis_village,
            "gis_area_sqm": props_area_sqm,
            "computed_metric_area_sqm": computed_metric_area_sqm,
            "textual_area_sqm": textual_area_sqm
        }

        # Area check
        diff_sqm = 0.0
        pct_diff = 0.0
        if textual_area_sqm and textual_area_sqm > 0:
            diff_sqm = abs(textual_area_sqm - props_area_sqm)
            pct_diff = round((diff_sqm / max(1.0, props_area_sqm)) * 100.0, 2)
            evidence["area_difference_sqm"] = diff_sqm
            evidence["area_difference_pct"] = pct_diff

            if pct_diff > error_tolerance_pct:
                severity = "error"
                deviations.append(f"critical_area_mismatch:{pct_diff}%>{error_tolerance_pct}%")
            elif pct_diff > warn_tolerance_pct:
                severity = "warn" if severity != "error" else severity
                deviations.append(f"moderate_area_mismatch:{pct_diff}%>{warn_tolerance_pct}%")

        # 2. Administrative check
        admin_mismatches = []
        if village and gis_village and village.lower() not in gis_village.lower() and gis_village.lower() not in village.lower():
            admin_mismatches.append(f"village_mismatch:doc='{village}'_gis='{gis_village}'")
        if tehsil and gis_tehsil and tehsil.lower() not in gis_tehsil.lower() and gis_tehsil.lower() not in tehsil.lower():
            admin_mismatches.append(f"tehsil_mismatch:doc='{tehsil}'_gis='{gis_tehsil}'")
        if district and gis_district and district.lower() not in gis_district.lower() and gis_district.lower() not in district.lower():
            admin_mismatches.append(f"district_mismatch:doc='{district}'_gis='{gis_district}'")

        if admin_mismatches:
            severity = "error"
            deviations.extend(admin_mismatches)
            evidence["admin_mismatches"] = admin_mismatches

        # 3. Neighbour Boundary Check
        cadastral_neighbours = props.get("neighbours", [])
        evidence["cadastral_neighbours"] = cadastral_neighbours
        neighbour_mismatches = []
        if boundaries:
            for direction, b_val in boundaries.items():
                clean_b = str(b_val).strip().lower()
                # Check if direction survey is in neighbours list
                if not any(clean_b in str(cn).lower() for cn in cadastral_neighbours):
                    neighbour_mismatches.append(f"{direction}_neighbour_unmatched:doc='{b_val}'")

            if neighbour_mismatches:
                severity = "warn" if severity != "error" else severity
                deviations.extend(neighbour_mismatches)
                evidence["neighbour_mismatches"] = neighbour_mismatches

        # 4. Shape sanity & sliver check
        poly = shape(geom)
        shape_stats = check_shape_sanity(poly)
        evidence["shape_stats"] = shape_stats
        if not shape_stats["is_valid"]:
            severity = "error"
            deviations.append(f"invalid_polygon_geometry:{shape_stats['validity_reason']}")
        elif shape_stats["is_sliver"]:
            severity = "warn" if severity != "error" else severity
            deviations.append(f"sliver_polygon_detected:compactness={shape_stats['compactness_score']}")

        # 5. Overlap check with other parcels
        overlaps = self.check_parcel_overlaps(feat)
        if overlaps:
            severity = "error"
            deviations.append(f"cadastral_overlap_detected:{len(overlaps)}_parcels")
            evidence["overlaps"] = overlaps

        # Neighbour features for map rendering
        neighbour_features = self.get_neighbour_features(cadastral_neighbours)

        # Message generation
        if severity == "error":
            message = f"Cadastral check failed with critical discrepancies: {'; '.join(deviations)}"
        elif severity == "warn":
            message = f"Cadastral check flagged advisory warnings: {'; '.join(deviations)}"
        else:
            message = "Cadastral cross-check verified: Polygon geometry, area, and administrative hierarchy align."

        return {
            "matched": True,
            "status": severity,
            "message": message,
            "ulpin": matched_ulpin,
            "gis_area_sqm": props_area_sqm,
            "textual_area_sqm": textual_area_sqm,
            "discrepancy_pct": pct_diff,
            "deviations": deviations,
            "evidence": evidence,
            "matched_parcel_feature": feat,
            "neighbour_features": neighbour_features
        }

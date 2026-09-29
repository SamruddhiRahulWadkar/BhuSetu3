"""
Cadastral GIS Integration Adapter.
Provides spatial parcel lookups by ULPIN (Bhu-Aadhaar), coordinates, and survey number,
integrating cadastral vector layers with digitized text records.
"""

import os
import json
from typing import Dict, Any, Optional, List
from shapely.geometry import shape, Point, mapping

CADASTRAL_FILE_PATH = os.path.join("data", "cadastre", "parcels.geojson")


class CadastralGISAdapter:
    """Adapter for spatial parcel queries and cadastral GIS layers."""

    def __init__(self, geojson_path: Optional[str] = None):
        self.geojson_path = geojson_path or CADASTRAL_FILE_PATH
        self._geojson_data = None
        self._load_geojson()

    def _load_geojson(self):
        if os.path.exists(self.geojson_path):
            with open(self.geojson_path, "r", encoding="utf-8") as f:
                self._geojson_data = json.load(f)
        else:
            self._geojson_data = {"type": "FeatureCollection", "features": []}

    def get_parcel_by_ulpin(self, ulpin: str) -> Optional[Dict[str, Any]]:
        """Finds a parcel by its 14-digit standard ULPIN."""
        norm_ulpin = ulpin.strip().upper()
        for feat in self._geojson_data.get("features", []):
            props = feat.get("properties", {})
            if str(props.get("ulpin", "")).upper() == norm_ulpin:
                return feat
        return None

    def get_parcel_by_survey_no(self, village: str, survey_no: str) -> Optional[Dict[str, Any]]:
        """Finds a parcel by village name and survey/khasra number."""
        norm_v = village.strip().lower()
        norm_s = str(survey_no).strip()
        for feat in self._geojson_data.get("features", []):
            props = feat.get("properties", {})
            if (
                props.get("village", "").strip().lower() == norm_v
                and str(props.get("survey_no", "")).strip() == norm_s
            ):
                return feat
        return None

    def query_parcels_by_village(self, village: str) -> Dict[str, Any]:
        """Returns all cadastral parcels in GeoJSON format for a specific village."""
        norm_v = village.strip().lower()
        matched = [
            f for f in self._geojson_data.get("features", [])
            if f.get("properties", {}).get("village", "").strip().lower() == norm_v
        ]
        return {
            "type": "FeatureCollection",
            "name": f"Cadastre_{village}",
            "features": matched
        }

    def find_parcel_at_point(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Reverse geocoding: returns the parcel polygon containing coordinates (lat, lon)."""
        pt = Point(lon, lat)
        for feat in self._geojson_data.get("features", []):
            poly = shape(feat["geometry"])
            if poly.contains(pt):
                return feat
        return None

    def get_all_parcels(self) -> Dict[str, Any]:
        """Returns the full Cadastral FeatureCollection."""
        return self._geojson_data

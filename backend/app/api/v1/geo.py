import os
import json
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from backend.app.geo_crosscheck.checker import CadastralGeoCrossChecker, GEOJSON_PATH

router = APIRouter(prefix="/geo", tags=["Geospatial"])
checker = CadastralGeoCrossChecker()


@router.get("/cadastre")
def get_cadastre_geojson():
    """Returns the complete 40-parcel Cadastral GeoJSON layer with ULPINs and survey boundaries."""
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}


@router.get("/crosscheck")
def cross_check_survey(
    survey_no: str = Query(..., description="Survey or Khasra Number"),
    village: Optional[str] = Query("", description="Village Name"),
    textual_area_sqm: Optional[float] = Query(None, description="Recorded textual area in sq metres")
):
    """Cross-validates document survey area against cadastral GIS parcel boundary."""
    res = checker.cross_check(survey_no, village or "", textual_area_sqm)
    return res

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ConfidenceBreakdown(BaseModel):
    ocr: float = Field(default=0.0, description="Raw OCR or LLM vision self-confidence")
    agreement: float = Field(default=1.0, description="Cross-engine agreement score")
    damage_penalty: float = Field(default=0.0, description="Penalty deducted for local blur/fade/stain under bbox")
    format: float = Field(default=1.0, description="Regex and checksum format validity score")
    consistency: float = Field(default=1.0, description="Validation consistency across related fields")
    final: float = Field(default=0.0, description="Calibrated final confidence score (0.0 to 1.0)")


class FieldItem(BaseModel):
    """
    Mandatory representation of every extracted field in BhuSetu.
    Rule: Every extracted field is an object: {value, raw_text, confidence, bbox, source_engine, flags[]}.
    Never return bare strings.
    """
    value: Optional[Any] = None
    raw_text: str = ""
    confidence: float = 0.0
    bbox: List[float] = Field(default_factory=list, description="[ymin, xmin, ymax, xmax] normalized (0.0 to 1.0)")
    source_engine: str = "gemini"  # gemini, tesseract, ensemble, mock
    flags: List[str] = Field(default_factory=list, description="Explainability and normalization flags")
    confidence_breakdown: Optional[ConfidenceBreakdown] = None


class OwnerShareItem(BaseModel):
    name: FieldItem
    father_or_husband_name: Optional[FieldItem] = None
    share: FieldItem
    is_minor: Optional[FieldItem] = None
    is_deceased: Optional[FieldItem] = None


class MutationRecordItem(BaseModel):
    mutation_no: FieldItem
    mutation_date: Optional[FieldItem] = None
    registration_date: Optional[FieldItem] = None
    mutation_type: Optional[FieldItem] = None  # sale, inheritance, partition, gift
    from_party: Optional[FieldItem] = None
    to_party: Optional[FieldItem] = None
    transferred_area: Optional[FieldItem] = None
    order_ref: Optional[FieldItem] = None
    status: Optional[FieldItem] = None


class RegistrationDetailItem(BaseModel):
    reg_no: FieldItem
    reg_date: Optional[FieldItem] = None
    sub_registrar_office: Optional[FieldItem] = None
    stamp_duty_paid: Optional[FieldItem] = None


class PlotAreaItem(BaseModel):
    value: FieldItem
    unit: FieldItem
    area_sqm: Optional[FieldItem] = None
    area_hectares: Optional[FieldItem] = None


class LandRecordExtraction(BaseModel):
    """
    Strict extraction schema covering Khatauni/7-12, Mutation Register, and Sale Deed summaries.
    """
    document_type: FieldItem
    state: FieldItem
    district: FieldItem
    tehsil: FieldItem
    village: FieldItem
    survey_no: FieldItem
    khasra_no: Optional[FieldItem] = None
    khata_no: Optional[FieldItem] = None
    sub_division: Optional[FieldItem] = None
    ulpin: Optional[FieldItem] = None

    plot_area: PlotAreaItem
    land_classification: FieldItem
    ownership_type: Optional[FieldItem] = None  # freehold, restricted_tenure, government, inam

    landowners: List[OwnerShareItem] = Field(default_factory=list)
    mutation_entries: List[MutationRecordItem] = Field(default_factory=list)
    registration: Optional[RegistrationDetailItem] = None

    encumbrances_or_loans: Optional[FieldItem] = None
    remarks_or_annotations: Optional[FieldItem] = None
    na_conversion_order_ref: Optional[FieldItem] = None
    restricted_tenure_permission_ref: Optional[FieldItem] = None

    def get_all_fields_flat(self) -> Dict[str, FieldItem]:
        """Flattens all FieldItems for uniform normalization, confidence calibration, and routing."""
        flat: Dict[str, FieldItem] = {}
        flat["document_type"] = self.document_type
        flat["state"] = self.state
        flat["district"] = self.district
        flat["tehsil"] = self.tehsil
        flat["village"] = self.village
        flat["survey_no"] = self.survey_no
        if self.khasra_no: flat["khasra_no"] = self.khasra_no
        if self.khata_no: flat["khata_no"] = self.khata_no
        if self.sub_division: flat["sub_division"] = self.sub_division
        if self.ulpin: flat["ulpin"] = self.ulpin
        flat["plot_area_value"] = self.plot_area.value
        flat["plot_area_unit"] = self.plot_area.unit
        flat["land_classification"] = self.land_classification
        if self.ownership_type: flat["ownership_type"] = self.ownership_type
        if self.encumbrances_or_loans: flat["encumbrances"] = self.encumbrances_or_loans
        if self.remarks_or_annotations: flat["remarks"] = self.remarks_or_annotations
        if self.na_conversion_order_ref: flat["na_order_ref"] = self.na_conversion_order_ref
        if self.restricted_tenure_permission_ref: flat["tenure_perm_ref"] = self.restricted_tenure_permission_ref

        for idx, owner in enumerate(self.landowners):
            flat[f"owner_{idx}_name"] = owner.name
            flat[f"owner_{idx}_share"] = owner.share
            if owner.father_or_husband_name:
                flat[f"owner_{idx}_father_husband"] = owner.father_or_husband_name
            if owner.is_minor:
                flat[f"owner_{idx}_is_minor"] = owner.is_minor
            if owner.is_deceased:
                flat[f"owner_{idx}_is_deceased"] = owner.is_deceased

        for idx, mut in enumerate(self.mutation_entries):
            flat[f"mutation_{idx}_no"] = mut.mutation_no
            if mut.mutation_date: flat[f"mutation_{idx}_date"] = mut.mutation_date
            if mut.registration_date: flat[f"mutation_{idx}_reg_date"] = mut.registration_date
            if mut.from_party: flat[f"mutation_{idx}_from"] = mut.from_party
            if mut.to_party: flat[f"mutation_{idx}_to"] = mut.to_party
            if mut.transferred_area: flat[f"mutation_{idx}_area"] = mut.transferred_area
            if mut.order_ref: flat[f"mutation_{idx}_order_ref"] = mut.order_ref

        if self.registration:
            flat["reg_no"] = self.registration.reg_no
            if self.registration.reg_date: flat["reg_date"] = self.registration.reg_date
            if self.registration.sub_registrar_office: flat["sub_registrar_office"] = self.registration.sub_registrar_office

        return flat

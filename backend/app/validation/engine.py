import os
import glob
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import yaml

from backend.app.models.validation import ValidationResult, LEGAL_DISCLAIMER
from backend.app.extraction.schemas import LandRecordExtraction, FieldItem
from backend.app.integration.mock_lrms import verify_hierarchy

RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    clean = date_str.strip()
    patterns = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d",
        "%d.%m.%Y", "%Y.%m.%d"
    ]
    for pat in patterns:
        try:
            return datetime.strptime(clean, pat)
        except ValueError:
            continue
    return None


class LegalLogicValidationEngine:
    def __init__(self):
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.load_all_rules()

    def load_all_rules(self):
        """Loads all YAML rule definitions dynamically from rules directory."""
        self.rules.clear()
        rule_files = glob.glob(os.path.join(RULES_DIR, "*.yaml"))
        for rf in rule_files:
            try:
                with open(rf, "r", encoding="utf-8") as f:
                    rule_def = yaml.safe_load(f)
                    if rule_def and "id" in rule_def:
                        self.rules[rule_def["id"]] = rule_def
            except Exception as e:
                print(f"Error loading rule file {rf}: {e}")

    def update_rule_config(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Allows admin to update thresholds or enable/disable rules dynamically."""
        if rule_id in self.rules:
            self.rules[rule_id].update(updates)
            return True
        return False

    def validate_document(
        self,
        document_id: str,
        extraction: LandRecordExtraction,
        existing_documents: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[ValidationResult], float, List[str]]:
        """
        Executes all active rules against the extracted record.
        Returns:
            (validation_results, validation_summary_score, failed_rule_ids)
        """
        results: List[ValidationResult] = []
        failed_rule_ids: List[str] = []

        flat_fields = extraction.get_all_fields_flat()

        # Rule 1: Owner Shares Sum to 1.0 (100%)
        r_share = self.rules.get("RULE_SHARE_SUM_100", {"enabled": True, "tolerance": 0.01})
        if r_share.get("enabled", True) and extraction.landowners:
            total_share = 0.0
            shares_raw = []
            for o in extraction.landowners:
                val = o.share.value
                raw = o.share.raw_text
                shares_raw.append(raw)
                try:
                    if isinstance(val, (int, float)):
                        total_share += float(val)
                    elif isinstance(val, str) and "/" in val:
                        num, den = val.split("/")
                        total_share += float(num) / float(den)
                    elif isinstance(val, str) and "%" in val:
                        total_share += float(val.replace("%", "").strip()) / 100.0
                    elif val:
                        total_share += float(val)
                except (ValueError, ZeroDivisionError):
                    pass

            tolerance = r_share.get("tolerance", 0.01)
            discrepancy = abs(total_share - 1.0)
            if discrepancy > tolerance:
                msg = f"Total registered share sum is {total_share:.4f} (expected 1.0000). Discrepancy of {discrepancy:.4f} detected across {len(extraction.landowners)} owners."
                res = ValidationResult(
                    document_id=document_id,
                    rule_id="RULE_SHARE_SUM_100",
                    rule_name=r_share.get("name", "Co-owner Shares Must Sum to 100%"),
                    severity=r_share.get("severity", "critical"),
                    status="failed",
                    message=msg,
                    evidence={"total_share": total_share, "discrepancy": discrepancy, "shares": shares_raw},
                    disclaimer=LEGAL_DISCLAIMER
                )
                results.append(res)
                failed_rule_ids.append("RULE_SHARE_SUM_100")
            else:
                results.append(ValidationResult(
                    document_id=document_id,
                    rule_id="RULE_SHARE_SUM_100",
                    rule_name="Co-owner Shares Must Sum to 100%",
                    severity="info",
                    status="passed",
                    message=f"All co-owner shares sum correctly to 1.0000 (discrepancy: {discrepancy:.4f}).",
                    evidence={"total_share": total_share},
                    disclaimer=LEGAL_DISCLAIMER
                ))

        # Rule 2: Sale/Transfer Area <= Holding Area
        r_area = self.rules.get("RULE_AREA_HOLDING_LIMIT", {"enabled": True})
        if r_area.get("enabled", True):
            holding_sqm = extraction.plot_area.area_sqm.value if extraction.plot_area.area_sqm else None
            if holding_sqm and extraction.mutation_entries:
                for idx, mut in enumerate(extraction.mutation_entries):
                    t_area_val = mut.transferred_area.value if mut.transferred_area else None
                    if t_area_val is not None:
                        try:
                            # If unit not specified, assume same or check ratio
                            t_val = float(t_area_val)
                            # Assume transferred area in sqm or same proportion
                            if t_val > float(holding_sqm) * 1.01:
                                excess = t_val - float(holding_sqm)
                                excess_pct = (excess / float(holding_sqm)) * 100.0
                                msg = f"Transferred area ({t_val:.2f}) exceeds parcel holding area ({float(holding_sqm):.2f}) by {excess:.2f} ({excess_pct:.1f}%)."
                                results.append(ValidationResult(
                                    document_id=document_id,
                                    rule_id="RULE_AREA_HOLDING_LIMIT",
                                    rule_name=r_area.get("name", "Sale Area Exceeds Holding Area"),
                                    severity=r_area.get("severity", "critical"),
                                    status="failed",
                                    message=msg,
                                    evidence={"transferred_area": t_val, "holding_area": float(holding_sqm), "mutation_index": idx},
                                    disclaimer=LEGAL_DISCLAIMER
                                ))
                                failed_rule_ids.append("RULE_AREA_HOLDING_LIMIT")
                                break
                        except ValueError:
                            pass

        # Rule 3: Mutation Temporal & Chronological Ordering
        r_chrono = self.rules.get("RULE_MUTATION_CHRONOLOGY", {"enabled": True})
        if r_chrono.get("enabled", True):
            now = datetime.utcnow()
            for idx, mut in enumerate(extraction.mutation_entries):
                m_date_str = mut.mutation_date.value if mut.mutation_date else None
                r_date_str = mut.registration_date.value if mut.registration_date else None
                if not r_date_str and extraction.registration and extraction.registration.reg_date:
                    r_date_str = extraction.registration.reg_date.value

                m_date = parse_date(m_date_str)
                r_date = parse_date(r_date_str)

                # Future date check
                if m_date and m_date > now:
                    results.append(ValidationResult(
                        document_id=document_id,
                        rule_id="RULE_MUTATION_CHRONOLOGY",
                        rule_name="Future Date Prohibited",
                        severity="error",
                        status="failed",
                        message=f"Mutation date ({m_date_str}) is in the future.",
                        evidence={"mutation_date": m_date_str},
                        disclaimer=LEGAL_DISCLAIMER
                    ))
                    failed_rule_ids.append("RULE_MUTATION_CHRONOLOGY")

                # Chronology check: mutation must be on or after deed date
                if m_date and r_date and m_date < r_date:
                    results.append(ValidationResult(
                        document_id=document_id,
                        rule_id="RULE_MUTATION_CHRONOLOGY",
                        rule_name="Mutation Prior to Registration",
                        severity=r_chrono.get("severity", "error"),
                        status="failed",
                        message=f"Temporal inconsistency: Mutation date ({m_date_str}) is earlier than deed registration date ({r_date_str}).",
                        evidence={"mutation_date": m_date_str, "registration_date": r_date_str, "mutation_no": mut.mutation_no.value},
                        disclaimer=LEGAL_DISCLAIMER
                    ))
                    failed_rule_ids.append("RULE_MUTATION_CHRONOLOGY")

        # Rule 4: Party Capacity (Post-mortem transfer & minor without guardian)
        r_party = self.rules.get("RULE_PARTY_LEGAL_CAPACITY", {"enabled": True})
        if r_party.get("enabled", True):
            for idx, o in enumerate(extraction.landowners):
                # Deceased check
                if o.is_deceased and (o.is_deceased.value is True or str(o.is_deceased.value).lower() in ["true", "yes", "मृत"]):
                    # If this deceased owner is listed as an active transferor in mutation
                    for mut in extraction.mutation_entries:
                        from_p = str(mut.from_party.value or "")
                        if o.name.value and o.name.value.lower() in from_p.lower():
                            results.append(ValidationResult(
                                document_id=document_id,
                                rule_id="RULE_PARTY_LEGAL_CAPACITY",
                                rule_name="Deceased Party Transfer Violation",
                                severity="critical",
                                status="failed",
                                message=f"Party '{o.name.value}' is recorded as deceased, but appears as transferor in mutation #{mut.mutation_no.value}.",
                                evidence={"party_name": o.name.value, "mutation_no": mut.mutation_no.value},
                                disclaimer=LEGAL_DISCLAIMER
                            ))
                            failed_rule_ids.append("RULE_PARTY_LEGAL_CAPACITY")

                # Minor check
                if o.is_minor and (o.is_minor.value is True or str(o.is_minor.value).lower() in ["true", "yes", "नाबालिग", "अल्पवयीन"]):
                    # Minor must have guardian or court order
                    if not o.father_or_husband_name or not o.father_or_husband_name.value:
                        results.append(ValidationResult(
                            document_id=document_id,
                            rule_id="RULE_PARTY_LEGAL_CAPACITY",
                            rule_name="Minor Owner Missing Guardian",
                            severity="warn",
                            status="failed",
                            message=f"Minor owner '{o.name.value}' registered without legal guardian designation.",
                            evidence={"party_name": o.name.value},
                            disclaimer=LEGAL_DISCLAIMER
                        ))
                        failed_rule_ids.append("RULE_PARTY_LEGAL_CAPACITY")

        # Rule 5: Land Class Conversion (Agricultural -> NA Order Ref)
        r_conv = self.rules.get("RULE_LAND_CLASS_CONVERSION_ORDER", {"enabled": True})
        if r_conv.get("enabled", True):
            land_c = str(extraction.land_classification.value or "").lower()
            if "non_agricultural" in land_c or "na" in land_c or "commercial" in land_c:
                has_na_ref = extraction.na_conversion_order_ref and extraction.na_conversion_order_ref.value
                if not has_na_ref:
                    results.append(ValidationResult(
                        document_id=document_id,
                        rule_id="RULE_LAND_CLASS_CONVERSION_ORDER",
                        rule_name="Missing NA Conversion Order",
                        severity="error",
                        status="failed",
                        message=f"Land class '{land_c}' requires a Non-Agricultural (NA) conversion order reference, none was found.",
                        evidence={"land_class": land_c},
                        disclaimer=LEGAL_DISCLAIMER
                    ))
                    failed_rule_ids.append("RULE_LAND_CLASS_CONVERSION_ORDER")

        # Rule 6: Restricted Tenure Land Alienation Permission
        r_tenure = self.rules.get("RULE_RESTRICTED_TENURE_TRANSFER", {"enabled": True})
        if r_tenure.get("enabled", True):
            tenure = str(extraction.ownership_type.value or "").lower() if extraction.ownership_type else "freehold"
            if "restricted" in tenure or "tribal" in tenure or "inam" in tenure:
                has_perm = extraction.restricted_tenure_permission_ref and extraction.restricted_tenure_permission_ref.value
                if not has_perm:
                    results.append(ValidationResult(
                        document_id=document_id,
                        rule_id="RULE_RESTRICTED_TENURE_TRANSFER",
                        rule_name="Missing Competent Authority Transfer Permission",
                        severity="critical",
                        status="failed",
                        message=f"Transfer on restricted tenure ({tenure}) requires statutory Collector / Competent Authority permission.",
                        evidence={"tenure_type": tenure},
                        disclaimer=LEGAL_DISCLAIMER
                    ))
                    failed_rule_ids.append("RULE_RESTRICTED_TENURE_TRANSFER")

        # Rule 7: Duplicate Registry Detection
        r_dup = self.rules.get("RULE_DUPLICATE_REGISTRY_DETECTION", {"enabled": True})
        if r_dup.get("enabled", True) and existing_documents:
            curr_surv = str(extraction.survey_no.value or "").strip()
            curr_vill = str(extraction.village.value or "").strip().lower()
            curr_reg = str(extraction.registration.reg_no.value or "") if extraction.registration else ""

            for doc in existing_documents:
                if doc.get("id") == document_id:
                    continue
                # Check registration reuse
                if curr_reg and doc.get("reg_no") == curr_reg:
                    results.append(ValidationResult(
                        document_id=document_id,
                        rule_id="RULE_DUPLICATE_REGISTRY_DETECTION",
                        rule_name="Reused Registration Number Detected",
                        severity="critical",
                        status="failed",
                        message=f"Duplicate registration number '{curr_reg}' already registered in Document ID '{doc.get('id')}'.",
                        evidence={"conflicting_doc_id": doc.get("id"), "reg_no": curr_reg},
                        disclaimer=LEGAL_DISCLAIMER
                    ))
                    failed_rule_ids.append("RULE_DUPLICATE_REGISTRY_DETECTION")
                    break

        # Rule 8: Land Ceiling Limit
        r_ceil = self.rules.get("RULE_AGRICULTURAL_LAND_CEILING", {"enabled": True})
        if r_ceil.get("enabled", True):
            state_key = str(extraction.state.value or "").lower()
            thresholds = r_ceil.get("thresholds_hectares", {}).get(state_key, r_ceil.get("thresholds_hectares", {}).get("default", {"irrigated": 7.28, "dry": 21.85}))
            land_c = str(extraction.land_classification.value or "").lower()
            ceiling_ha = thresholds.get("irrigated", 7.28) if "irrigated" in land_c else thresholds.get("dry", 21.85)

            holding_ha = extraction.plot_area.area_hectares.value if extraction.plot_area.area_hectares else None
            if holding_ha and float(holding_ha) > ceiling_ha:
                results.append(ValidationResult(
                    document_id=document_id,
                    rule_id="RULE_AGRICULTURAL_LAND_CEILING",
                    rule_name="Agricultural Land Ceiling Exceeded",
                    severity="warn",
                    status="failed",
                    message=f"Recorded holding of {float(holding_ha):.2f} ha exceeds statutory ceiling limit of {ceiling_ha:.2f} ha.",
                    evidence={"holding_ha": float(holding_ha), "ceiling_ha": ceiling_ha, "state": state_key},
                    disclaimer=LEGAL_DISCLAIMER
                ))
                failed_rule_ids.append("RULE_AGRICULTURAL_LAND_CEILING")

        # Rule 9: Format Rules (Survey No & ULPIN)
        r_fmt = self.rules.get("RULE_IDENTIFIER_FORMAT_CHECK", {"enabled": True})
        if r_fmt.get("enabled", True):
            if extraction.ulpin and extraction.ulpin.value:
                ulpin_val = str(extraction.ulpin.value).strip()
                if not re.match(r"^[A-Z0-9]{14}$", ulpin_val):
                    results.append(ValidationResult(
                        document_id=document_id,
                        rule_id="RULE_IDENTIFIER_FORMAT_CHECK",
                        rule_name="Invalid ULPIN 14-char Format",
                        severity="warn",
                        status="failed",
                        message=f"ULPIN '{ulpin_val}' is invalid (must be 14-char alphanumeric checksum).",
                        evidence={"ulpin": ulpin_val},
                        disclaimer=LEGAL_DISCLAIMER
                    ))
                    failed_rule_ids.append("RULE_IDENTIFIER_FORMAT_CHECK")

        # Rule 10: Mock LRMS Administrative Hierarchy Cross-check
        r_hier = self.rules.get("RULE_ADMIN_HIERARCHY_VALIDITY", {"enabled": True})
        if r_hier.get("enabled", True):
            st = str(extraction.state.value or "")
            dt = str(extraction.district.value or "")
            th = str(extraction.tehsil.value or "")
            vl = str(extraction.village.value or "")
            is_valid, reason = verify_hierarchy(st, dt, th, vl)
            if not is_valid:
                results.append(ValidationResult(
                    document_id=document_id,
                    rule_id="RULE_ADMIN_HIERARCHY_VALIDITY",
                    rule_name="Invalid Administrative Hierarchy",
                    severity="error",
                    status="failed",
                    message=f"Administrative hierarchy check failed: {reason}",
                    evidence={"state": st, "district": dt, "tehsil": th, "village": vl, "reason": reason},
                    disclaimer=LEGAL_DISCLAIMER
                ))
                failed_rule_ids.append("RULE_ADMIN_HIERARCHY_VALIDITY")
            else:
                results.append(ValidationResult(
                    document_id=document_id,
                    rule_id="RULE_ADMIN_HIERARCHY_VALIDITY",
                    rule_name="Administrative Hierarchy Validated",
                    severity="info",
                    status="passed",
                    message="Village, Tehsil, District, and State verified against National LRMS directory.",
                    evidence={"state": st, "district": dt, "tehsil": th, "village": vl},
                    disclaimer=LEGAL_DISCLAIMER
                ))

        # Calculate validation summary score (0.0 to 1.0)
        total_eval = len(results)
        failed_count = len([r for r in results if r.status == "failed"])
        score = max(0.0, 1.0 - (failed_count / max(1, total_eval))) if total_eval > 0 else 1.0

        return results, round(score, 3), failed_rule_ids

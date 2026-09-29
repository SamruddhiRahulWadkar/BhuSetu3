"""
LRMS (Land Records Management System) Integration Adapter.
Provides bidirectional sync with state land registry APIs (e.g. Mahabhulekh, UP Bhulekh, Bihar Bhumi).
"""

from typing import Dict, Any, Optional, List
from backend.app.integration.mock_lrms import LRMS_MASTER_DIRECTORY, verify_hierarchy


class LRMSAdapter:
    """Adapter for National and State Land Records Management Systems."""

    def __init__(self, api_endpoint: Optional[str] = None):
        self.api_endpoint = api_endpoint or "https://mock.lrms.gov.in/api/v1"

    def check_hierarchy(self, state: str, district: str, tehsil: str, village: str) -> Dict[str, Any]:
        """Validates revenue hierarchy against master directory."""
        valid, msg = verify_hierarchy(state, district, tehsil, village)
        return {
            "valid": valid,
            "message": msg,
            "state": state,
            "district": district,
            "tehsil": tehsil,
            "village": village
        }

    def fetch_survey_status(self, state: str, district: str, tehsil: str, village: str, survey_no: str) -> Dict[str, Any]:
        """
        Simulates query to state LRMS for official recorded land tenure.
        """
        valid_hier, msg = verify_hierarchy(state, district, tehsil, village)
        if not valid_hier:
            return {
                "found": False,
                "error": msg,
                "status": "hierarchy_mismatch"
            }

        # Mock official government state record
        return {
            "found": True,
            "state": state,
            "district": district,
            "tehsil": tehsil,
            "village": village,
            "survey_no": survey_no,
            "official_status": "active",
            "tenure_type": "bhumidhar_with_transferable_rights",
            "dispute_pending": False,
            "government_encumbrance": False,
            "ulpin_assigned": True
        }

    def get_supported_states(self) -> List[str]:
        return [s.title() for s in LRMS_MASTER_DIRECTORY.keys()]

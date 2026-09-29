"""
Mock Master Land Records Management System (LRMS) National Directory.
Simulates state/district/tehsil/village hierarchy and registered cadastral boundaries.
"""

from typing import Dict, List, Optional, Tuple

LRMS_MASTER_DIRECTORY: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "maharashtra": {
        "pune": {
            "haveli": ["Wagholi", "Kharadi", "Hadapsar", "Loni Kalbhor", "Manjri", "Undri"],
            "mulshi": ["Pirangut", "Paud", "Hinjawadi", "Maan", "Lavale"],
            "khed": ["Chakan", "Alandi", "Rajgurunagar", "Mahalunge"],
            "baramati": ["Malegaon", "Baramati Rural", "Supa", "Karkamb"]
        },
        "satara": {
            "karad": ["Ond", "Saidapur", "Kale", "Umbraj"],
            "wai": ["Bhuinj", "Pachwad", "Shirwal"]
        },
        "nagpur": {
            "nagpur rural": ["Besur", "Wadi", "Kamptee", "Hingna"]
        }
    },
    "uttar pradesh": {
        "lucknow": {
            "bakshi ka talab": ["Bargadi", "Asthi", "Kathwara", "Mandiaon"],
            "sarojini nagar": ["Amausi", "Banthra", "Natkur", "Gauri"],
            "malihabad": ["Saspan", "Kakori", "Rahimabad"]
        },
        "varanasi": {
            "pindra": ["Sindhora", "Phoolpur", "Babepur"],
            "sadar": ["Shivpur", "Kashi Rural", "Lohta"]
        }
    },
    "bihar": {
        "patna": {
            "danapur": ["Khagaul", "Digha", "Maner"],
            "phulwari sharif": ["Sampatchak", "Janipur", "Alawalpur"]
        }
    }
}


def verify_hierarchy(state: str, district: str, tehsil: str, village: str) -> Tuple[bool, str]:
    """
    Verifies if (village, tehsil, district, state) is a valid path in LRMS.
    Returns (is_valid, reason).
    """
    st = state.strip().lower() if state else ""
    dt = district.strip().lower() if district else ""
    th = tehsil.strip().lower() if tehsil else ""
    vl = village.strip().lower() if village else ""

    if st not in LRMS_MASTER_DIRECTORY:
        return False, f"State '{state}' not recognized in LRMS registry"

    districts = LRMS_MASTER_DIRECTORY[st]
    if dt not in districts:
        return False, f"District '{district}' not found in state '{state}'"

    tehsils = districts[dt]
    if th not in tehsils:
        return False, f"Tehsil '{tehsil}' not found in district '{district}', {state}"

    villages = [v.lower() for v in tehsils[th]]
    if vl not in villages:
        return False, f"Village '{village}' not mapped to tehsil '{tehsil}', {district}"

    return True, "Valid LRMS administrative hierarchy"

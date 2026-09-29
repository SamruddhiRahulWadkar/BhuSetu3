import pytest
from backend.app.normalization.normalizer import RegionalNormalizer


@pytest.fixture
def norm():
    return RegionalNormalizer()


def test_field_synonym_canonicalization(norm):
    canon, conf = norm.canonicalize_field_name("गट क्रमांक")
    assert canon == "survey_or_khasra_no"
    assert conf >= 0.90

    canon, conf = norm.canonicalize_field_name("खसरा संख्या")
    assert canon == "survey_or_khasra_no"

    canon, conf = norm.canonicalize_field_name("खातेदार क्रमांक")
    assert canon == "khata_no"


def test_land_class_normalization(norm):
    canon, flags = norm.normalize_land_class("बागायत")
    assert canon == "irrigated"
    assert any("normalized_land_class" in f for f in flags)

    canon, flags = norm.normalize_land_class("जिरायत")
    assert canon == "unirrigated_dry"

    canon, flags = norm.normalize_land_class("बिगरशेती")
    assert canon == "non_agricultural"


def test_area_unit_conversion(norm):
    # Standard unit: 10 guntha in Maharashtra
    sqm, ha, flags = norm.convert_area(10.0, "guntha", state="Maharashtra")
    assert round(sqm, 1) == 1011.7
    assert round(ha, 4) == 0.1012

    # State variable: 2 bigha in Uttar Pradesh
    sqm_up, ha_up, flags_up = norm.convert_area(2.0, "bigha", state="Uttar Pradesh")
    assert sqm_up > 5000.0

    # State variable without state context: requires warning flag
    sqm_unk, ha_unk, flags_unk = norm.convert_area(2.0, "bigha", state=None)
    assert any("warning:state_context_required" in f for f in flags_unk)


def test_indic_to_ascii_numerals(norm):
    # Devanagari numerals
    assert norm.indic_to_ascii_digits("१०३/२") == "103/2"
    assert norm.indic_to_ascii_digits("४०५०") == "4050"

    # Gujarati numerals
    assert norm.indic_to_ascii_digits("૧૦૧/૪") == "101/4"

    # Telugu numerals
    assert norm.indic_to_ascii_digits("౧౦౨") == "102"


def test_name_honorifics_and_fuzzy_matching(norm):
    # Honorific stripping
    cleaned = norm.strip_honorifics("श्री रमेश बापूराव पाटील")
    assert "श्री" not in cleaned

    # Transliteration
    trans = norm.transliterate_name("रमेश पाटील")
    assert "Ramesh" in trans
    assert "Patil" in trans

    # Cross-script fuzzy matching
    is_match, score, flags = norm.match_names("Ramesh Patil", "श्री रमेश पाटील")
    assert is_match is True
    assert score >= 0.75

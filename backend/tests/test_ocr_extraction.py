import os
import pytest
from backend.app.extraction.extractor import StructuredExtractor
from backend.app.extraction.schemas import FieldItem, LandRecordExtraction

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
SAMPLE_IMG = os.path.join(DATA_DIR, "samples", "record_01.png")


def test_extractor_offline_mock_mode():
    extractor = StructuredExtractor()
    extraction, agreements = extractor.extract_from_page(SAMPLE_IMG, filename_hint="record_01.png", force_mock=True)

    assert isinstance(extraction, LandRecordExtraction)

    # Verify strict FieldItem object representation rule:
    # "Every extracted field is an object: {value, raw_text, confidence, bbox, source_engine, flags[]}. Never return bare strings."
    fields_flat = extraction.get_all_fields_flat()
    for name, f in fields_flat.items():
        assert isinstance(f, FieldItem), f"Field {name} must be a FieldItem instance"
        assert hasattr(f, "value")
        assert hasattr(f, "raw_text")
        assert hasattr(f, "confidence")
        assert hasattr(f, "bbox")
        assert hasattr(f, "source_engine")
        assert hasattr(f, "flags")
        assert isinstance(f.flags, list)
        assert isinstance(f.confidence, float)

    # Survey number check
    assert extraction.survey_no.value is not None
    assert len(extraction.landowners) >= 1
    assert extraction.plot_area.value.value is not None

    # Agreements check
    assert len(agreements) > 0


def test_multi_page_merge():
    extractor = StructuredExtractor()
    ext1, _ = extractor.extract_from_page(SAMPLE_IMG, filename_hint="record_01.png", force_mock=True)
    ext2, _ = extractor.extract_from_page(SAMPLE_IMG, filename_hint="record_02.png", force_mock=True)

    merged = extractor.merge_multi_page([ext1, ext2])
    assert isinstance(merged, LandRecordExtraction)
    assert len(merged.landowners) >= len(ext1.landowners)

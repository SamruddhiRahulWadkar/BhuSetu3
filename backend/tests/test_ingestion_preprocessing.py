import os
import pytest
from PIL import Image
from backend.app.ingestion.service import IngestionService, compute_sha256
from backend.app.preprocessing.pipeline import PreprocessingPipeline
from backend.app.preprocessing.quality import analyze_page_quality
from backend.app.preprocessing.layout import LayoutDetector
from backend.app.models.document import Document
from backend.app.models.audit import AuditLog

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
SAMPLE_IMG = os.path.join(DATA_DIR, "samples", "record_01.png")


def test_sha256_computation():
    assert os.path.exists(SAMPLE_IMG), "Sample image record_01.png must exist"
    sha = compute_sha256(SAMPLE_IMG)
    assert len(sha) == 64
    assert isinstance(sha, str)


def test_quality_metrics_analyzer():
    with Image.open(SAMPLE_IMG) as img:
        metrics = analyze_page_quality(img, grid_rows=3, grid_cols=3)

        assert "blur_score" in metrics
        assert "contrast_score" in metrics
        assert "fade_score" in metrics
        assert "noise_score" in metrics
        assert "skew_angle" in metrics
        assert "tile_metrics" in metrics

        assert len(metrics["tile_metrics"]) == 9
        first_tile = metrics["tile_metrics"][0]
        assert "bbox" in first_tile
        assert len(first_tile["bbox"]) == 4
        assert "blur" in first_tile
        assert "fade" in first_tile


def test_preprocessing_pipeline(tmp_path):
    proc = PreprocessingPipeline()
    out_file = str(tmp_path / "proc_01.png")
    res = proc.process(SAMPLE_IMG, out_file)

    assert os.path.exists(out_file)
    assert "original_quality_metrics" in res
    assert "skew_corrected_degrees" in res


def test_layout_detector():
    detector = LayoutDetector()
    cls_res = detector.classify_document_type("खतौनी नकल 7/12 अधिकार अभिलेख")
    assert cls_res["doc_type"] == "khatauni_7_12"
    assert cls_res["confidence"] >= 0.90

    with Image.open(SAMPLE_IMG) as img:
        regions = detector.detect_regions(img)
        assert "tables" in regions
        assert len(regions["tables"]) >= 1
        assert "handwritten" in regions


def test_ingestion_service(db):
    doc = IngestionService.ingest_file(
        db=db,
        temp_file_path=SAMPLE_IMG,
        filename="record_01.png",
        mime_type="image/png",
        uploader_id="test_officer"
    )

    assert doc.id is not None
    assert doc.original_sha256 is not None
    assert doc.file_size > 0
    assert len(doc.pages) >= 1

    page = doc.pages[0]
    assert page.quality_metrics is not None
    assert "tile_metrics" in page.quality_metrics
    assert page.layout_data is not None

    # Verify audit log was emitted
    audit = db.query(AuditLog).filter(AuditLog.document_id == doc.id).first()
    assert audit is not None
    assert audit.action in ["DOCUMENT_UPLOADED", "DOCUMENT_PREPROCESSED"]

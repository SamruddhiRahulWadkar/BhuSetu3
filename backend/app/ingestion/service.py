import os
import hashlib
import uuid
import shutil
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from PIL import Image

from backend.app.config import settings
from backend.app.models.document import Document, Page
from backend.app.audit.logger import log_event
from backend.app.ingestion.pdf_converter import convert_pdf_to_images
from backend.app.preprocessing.pipeline import PreprocessingPipeline
from backend.app.preprocessing.layout import LayoutDetector
from backend.app.preprocessing.quality import sanitize_for_json

pipeline = PreprocessingPipeline()
layout_detector = LayoutDetector()


def compute_sha256(file_path: str) -> str:
    """Computes cryptographic SHA-256 digest for immutable record verification."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


class IngestionService:
    @staticmethod
    def ingest_file(
        db: Session,
        temp_file_path: str,
        filename: str,
        mime_type: str,
        uploader_id: Optional[str] = "officer_1"
    ) -> Document:
        """
        Ingests a land record document:
        1. Calculates SHA-256 hash
        2. Immutably stores original file in STORAGE_DIR/originals/<hash>.<ext>
        3. Converts PDF pages or copies image pages
        4. Runs preprocessing & tile-level quality assessment on each page
        5. Performs layout analysis (doc_type, tables, handwritten)
        6. Emits structured audit logs
        """
        # 1. Compute SHA-256
        sha256_hash = compute_sha256(temp_file_path)
        file_size = os.path.getsize(temp_file_path)

        # Check duplicate scan
        existing = db.query(Document).filter(Document.original_sha256 == sha256_hash).first()
        if existing:
            log_event(
                db,
                action="UPLOAD_DUPLICATE_DETECTED",
                document_id=existing.id,
                user_id=uploader_id,
                details={"filename": filename, "sha256": sha256_hash}
            )
            return existing

        # 2. Immutable storage
        ext = os.path.splitext(filename)[1].lower()
        storage_filename = f"{sha256_hash}{ext}"
        storage_path = os.path.join(settings.STORAGE_DIR, "originals", storage_filename)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        shutil.copy2(temp_file_path, storage_path)

        # 3. Create Document record
        doc = Document(
            filename=filename,
            original_sha256=sha256_hash,
            mime_type=mime_type,
            file_size=file_size,
            storage_path=storage_path,
            uploader_id=uploader_id,
            status="uploaded"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        log_event(
            db,
            action="DOCUMENT_UPLOADED",
            document_id=doc.id,
            user_id=uploader_id,
            details={"filename": filename, "size_bytes": file_size, "sha256": sha256_hash}
        )

        # 4. Convert pages
        pages_dir = os.path.join(settings.STORAGE_DIR, "pages", doc.id)
        processed_dir = os.path.join(settings.STORAGE_DIR, "processed", doc.id)
        os.makedirs(pages_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)

        if "pdf" in mime_type.lower() or ext == ".pdf":
            page_image_paths = convert_pdf_to_images(storage_path, pages_dir)
        else:
            dest_page_img = os.path.join(pages_dir, "page_001.png")
            shutil.copy2(storage_path, dest_page_img)
            page_image_paths = [dest_page_img]

        # 5. Preprocess each page & assess quality
        for idx, p_img_path in enumerate(page_image_paths, start=1):
            proc_img_path = os.path.join(processed_dir, f"page_{idx:03d}_processed.png")
            preprocess_result = pipeline.process(p_img_path, proc_img_path)

            # Layout detection
            with Image.open(proc_img_path) as p_img:
                layout_data = layout_detector.detect_regions(p_img)
                w, h = p_img.size

            page_rec = Page(
                document_id=doc.id,
                page_number=idx,
                image_path=p_img_path,
                processed_image_path=proc_img_path,
                width=w,
                height=h,
                quality_metrics=sanitize_for_json(preprocess_result["original_quality_metrics"]),
                layout_data=sanitize_for_json(layout_data)
            )
            db.add(page_rec)

        # Classify document type based on first page heuristics
        first_page_metrics = preprocess_result["original_quality_metrics"]
        type_class = layout_detector.classify_document_type(filename)
        doc.doc_type = type_class["doc_type"]
        doc.doc_type_confidence = type_class["confidence"]
        doc.status = "preprocessed"
        doc.processed_path = os.path.join(processed_dir, "page_001_processed.png")

        db.commit()
        db.refresh(doc)

        log_event(
            db,
            action="DOCUMENT_PREPROCESSED",
            document_id=doc.id,
            user_id=uploader_id,
            details={
                "pages_count": len(page_image_paths),
                "doc_type": doc.doc_type,
                "doc_type_confidence": doc.doc_type_confidence,
                "blur_score": first_page_metrics.get("blur_score"),
                "contrast_score": first_page_metrics.get("contrast_score")
            }
        )

        return doc

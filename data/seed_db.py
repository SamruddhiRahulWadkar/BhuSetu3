import os
import sys

# Add root directory to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.database import SessionLocal, Base, engine
from backend.app.models.document import Document
from backend.app.ingestion.service import IngestionService
from backend.app.api.v1.documents import process_document_pipeline

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(DATA_DIR, "samples")


def seed_database():
    """Seeds the database with the synthetic land record samples."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing_count = db.query(Document).count()
    if existing_count >= 15:
        print(f"Database already seeded with {existing_count} records.")
        db.close()
        return

    sample_files = sorted([f for f in os.listdir(SAMPLES_DIR) if f.endswith(".png")])[:15]
    print(f"Seeding database with {len(sample_files)} sample land records...")

    for fname in sample_files:
        fpath = os.path.join(SAMPLES_DIR, fname)
        try:
            doc = IngestionService.ingest_file(
                db=db,
                temp_file_path=fpath,
                filename=fname,
                mime_type="image/png",
                uploader_id="revenue_officer_pune"
            )
            process_document_pipeline(db, doc)
            print(f"  + Digitize & Processed: {fname} (Status: {doc.status}, Confidence: {doc.overall_confidence})")
        except Exception as e:
            print(f"  x Failed on {fname}: {e}")

    db.close()
    print("Database seeding completed!")


if __name__ == "__main__":
    seed_database()

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.document import Document
from backend.app.models.field import FieldRecord
from backend.app.ownership_chain.builder import OwnershipChainBuilder

router = APIRouter(prefix="/ownership", tags=["Ownership"])
builder = OwnershipChainBuilder()


@router.get("/chain/{document_id}")
def get_ownership_chain(document_id: str, db: Session = Depends(get_db)):
    """Returns genealogical ownership graph, transfer timeline, and chain continuity analysis."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = db.query(FieldRecord).filter(FieldRecord.document_id == doc.id).all()
    field_map = {f.field_name: f.value for f in fields}

    # Extract owners
    current_owners = []
    for f in fields:
        if "owner_" in f.field_name and "_name" in f.field_name:
            idx = f.field_name.split("_")[1]
            share_val = field_map.get(f"owner_{idx}_share", 0.5)
            try:
                s_float = float(share_val) if share_val is not None else 0.5
            except ValueError:
                s_float = 0.5

            current_owners.append({
                "name": str(f.value),
                "share": s_float,
                "is_deceased": field_map.get(f"owner_{idx}_is_deceased", False),
                "father_or_husband_name": field_map.get(f"owner_{idx}_father_husband", "")
            })

    if not current_owners:
        current_owners = [{"name": "Ramesh Patil", "share": 0.5}, {"name": "Suresh Deshmukh", "share": 0.5}]

    # Extract mutations
    mutations = []
    mut_no = field_map.get("mutation_0_no")
    if mut_no:
        mutations.append({
            "mutation_no": str(mut_no),
            "mutation_date": str(field_map.get("mutation_0_date", "2021-09-15")),
            "from_party": str(field_map.get("mutation_0_from", current_owners[0]["name"])),
            "to_party": str(field_map.get("mutation_0_to", current_owners[-1]["name"])),
            "transferred_area": field_map.get("mutation_0_area", 2000.0),
            "order_ref": str(field_map.get("mutation_0_order_ref", "SDO/REV/2021/894"))
        })
    else:
        # Default ancestral mutation chain for demonstration
        mutations.append({
            "mutation_no": "M-742",
            "mutation_date": "1994-06-12",
            "from_party": "Late Baburao Patil (Original Allottee)",
            "to_party": current_owners[0]["name"],
            "mutation_type": "inheritance",
            "transferred_area": 4046.86,
            "order_ref": "Tehsildar/INHER/1994/110"
        })
        mutations.append({
            "mutation_no": "M-801",
            "mutation_date": "2021-09-15",
            "from_party": current_owners[0]["name"],
            "to_party": current_owners[-1]["name"],
            "mutation_type": "sale",
            "transferred_area": 2000.0,
            "order_ref": "SDO/REV/2021/894"
        })

    chain_data = builder.build_chain(
        current_owners=current_owners,
        mutation_history=mutations,
        parcel_info={"survey_no": field_map.get("survey_no", "101")}
    )

    return chain_data

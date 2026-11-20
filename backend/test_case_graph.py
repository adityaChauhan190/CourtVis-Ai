"""Test graph extraction directly on case c32e4e5b-3eac-42af-abce-3234e5d55648."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.case import Case
from app.models.document import Document, DocumentStatus
from app.storage.local import storage_service
from app.api.routes.graph import get_evidence_graph
from app.schemas.document import UserContext

db = SessionLocal()
case_id = "c32e4e5b-3eac-42af-abce-3234e5d55648"

case = db.query(Case).filter(Case.id == case_id).first()
print(f"Case found: {case.name if case else 'NONE'}")
if case:
    print(f"Owner ID: {case.owner_id}")
    print(f"Cached evidence_graph: {bool(case.evidence_graph)}")
    docs = db.query(Document).filter(Document.case_id == case_id).all()
    print(f"Documents total: {len(docs)}")
    for d in docs:
        print(f"  Doc: {d.id} | Name: {d.original_name} | Status: {d.status} | Storage: {d.storage_path}")

    # Now let's try invoking the graph logic directly
    user_ctx = UserContext(id=case.owner_id, email="test@test.com", name="Test User")
    try:
        print("\n--- Invoking get_evidence_graph ---")
        res = get_evidence_graph(
            case_id=case_id,
            force_refresh=True,
            current_user=user_ctx,
            db=db,
            store=storage_service,
        )
        print("Success! Got nodes:", len(res.nodes), "edges:", len(res.edges))
    except Exception as e:
        import traceback
        print("Failed with error:")
        traceback.print_exc()

db.close()

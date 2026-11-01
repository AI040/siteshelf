from fastapi import APIRouter, File, UploadFile

from app.api.deps import DbSession
from app.core.config import get_settings
from app.schemas.upload import RejectedRow, UploadResponse
from app.services import upload_service
from app.services.upload_service import UploadOutcome

router = APIRouter(prefix="/websites", tags=["websites"])


# Plain `def`: pandas and SQLAlchemy are blocking, so FastAPI runs this in its
# thread pool and the event loop stays free.
@router.post("/upload", response_model=UploadResponse)
def upload_websites(session: DbSession, file: UploadFile = File(...)) -> UploadResponse:
    """Upload a CSV / Excel file; new sites are inserted, known sites get a fresh updated_at."""
    settings = get_settings()
    # Read one byte over the limit so an oversized file is detected without
    # loading all of it into memory.
    content = file.file.read(settings.max_upload_bytes + 1)
    outcome = upload_service.import_upload(session, content, file.filename or "")
    return _to_response(outcome, settings.rejected_preview_limit)


def _to_response(outcome: UploadOutcome, preview_limit: int) -> UploadResponse:
    rejected = outcome.rejected
    preview = rejected.head(preview_limit).astype(object)
    preview = preview.where(preview.notna(), None).to_dict("records")
    return UploadResponse(
        rows_in_file=outcome.rows_in_file,
        duplicates_in_file=outcome.duplicates_in_file,
        inserted=outcome.inserted,
        existing=outcome.existing,
        rejected=len(rejected),
        rejected_rows=[RejectedRow(**row) for row in preview],
        rejected_rows_truncated=len(rejected) > preview_limit,
    )

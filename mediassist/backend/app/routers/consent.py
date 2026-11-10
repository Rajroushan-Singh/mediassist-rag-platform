from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import ConsentRecord, User
from app.schemas import ConsentCreate, ConsentResponse

router = APIRouter(prefix="/consent", tags=["Consent"])


@router.post(
    "",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_consent(
    request: ConsentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Append an acceptance or withdrawal event; prior history is retained."""
    consent = ConsentRecord(
        user_id=current_user.id,
        consent_type=request.consent_type,
        consent_version=request.consent_version,
        accepted=request.accepted,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


@router.get("", response_model=list[ConsentResponse])
def get_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ConsentRecord)
        .filter(ConsentRecord.user_id == current_user.id)
        .order_by(ConsentRecord.accepted_at.desc(), ConsentRecord.id.desc())
        .all()
    )

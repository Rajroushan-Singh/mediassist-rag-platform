import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import ConsentRecord, User
from app.security import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        ) from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_health_information_consent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Require current-version consent for health chat and health records."""
    latest = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == current_user.id,
            ConsentRecord.consent_type == "health_information",
        )
        .order_by(ConsentRecord.accepted_at.desc(), ConsentRecord.id.desc())
        .first()
    )
    if (
        latest is None
        or not latest.accepted
        or latest.consent_version != settings.HEALTH_CONSENT_VERSION
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accept the current health-information consent before using chat or health records.",
        )
    return current_user

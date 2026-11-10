from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings


password_hasher = PasswordHasher()


def hash_password(password: str) -> str:

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    try:

        return password_hasher.verify(
            hashed_password,
            plain_password
        )

    except VerifyMismatchError:

        return False

    except Exception:

        return False


def create_access_token(user_id: int) -> str:

    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expiration,
        "iat": datetime.now(timezone.utc)
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str):

    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM]
    )
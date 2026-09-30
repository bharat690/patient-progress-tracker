from google.auth import exceptions as google_auth_exceptions
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from requests.exceptions import RequestException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


class GoogleAuthNotConfigured(Exception):
    pass


class InvalidGoogleCredential(Exception):
    pass


class GoogleVerificationUnavailable(Exception):
    pass


class GoogleAccountConflict(Exception):
    pass


def authenticate_google_user(
    db: Session,
    credential: str,
    client_id: str | None,
) -> User:
    if not client_id:
        raise GoogleAuthNotConfigured

    try:
        claims = id_token.verify_oauth2_token(
            credential,
            Request(),
            client_id,
        )
    except ValueError as exc:
        raise InvalidGoogleCredential from exc
    except (google_auth_exceptions.GoogleAuthError, RequestException) as exc:
        raise GoogleVerificationUnavailable from exc

    subject = claims.get("sub")
    email = claims.get("email")
    if (
        not isinstance(subject, str)
        or not subject
        or not isinstance(email, str)
        or not email
        or claims.get("email_verified") is not True
    ):
        raise InvalidGoogleCredential

    normalized_email = email.strip().lower()
    if len(normalized_email) > 255:
        raise InvalidGoogleCredential

    identity_user = db.scalar(
        select(User).where(User.google_subject == subject)
    )
    email_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if identity_user is not None:
        if email_user is not None and email_user.id != identity_user.id:
            raise GoogleAccountConflict
        identity_user.email = normalized_email
        user = identity_user
    elif email_user is not None:
        if email_user.google_subject not in (None, subject):
            raise GoogleAccountConflict
        email_user.google_subject = subject
        user = email_user
    else:
        name = claims.get("name")
        safe_name = (
            " ".join(name.split())[:100]
            if isinstance(name, str) and name.strip()
            else normalized_email.split("@", maxsplit=1)[0][:100]
        )
        user = User(
            name=safe_name,
            email=normalized_email,
            password_hash=None,
            google_subject=subject,
            role="doctor",
            is_active=True,
        )
        db.add(user)

    if not user.is_active:
        raise InvalidGoogleCredential

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise GoogleAccountConflict from exc

    db.refresh(user)
    return user

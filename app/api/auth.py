from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import GOOGLE_CLIENT_ID
from app.core.rate_limit import enforce_rate_limit
from app.core.security import create_access_token
from app.db.postgres import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import GoogleCredential, TokenResponse, UserPublic
from app.services.google_auth import (
    GoogleAccountConflict,
    GoogleAuthNotConfigured,
    GoogleVerificationUnavailable,
    InvalidGoogleCredential,
    authenticate_google_user,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/google", response_model=TokenResponse)
def google_login(
    payload: GoogleCredential,
    request: Request,
    db: Session = Depends(get_db),
):
    client_key = request.client.host if request.client else "anonymous"
    try:
        enforce_rate_limit("LOGIN", client_key)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    try:
        user = authenticate_google_user(
            db,
            payload.credential,
            GOOGLE_CLIENT_ID,
        )
    except GoogleAuthNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured",
        ) from exc
    except InvalidGoogleCredential as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google sign-in could not be verified",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except GoogleVerificationUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in verification is temporarily unavailable",
        ) from exc
    except GoogleAccountConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Google account conflicts with an existing account",
        ) from exc

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
    }


@router.post("/register", include_in_schema=False)
def password_registration_disabled():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Password registration has been replaced by Google sign-in",
    )


@router.post("/login", include_in_schema=False)
def password_login_disabled():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Password login has been replaced by Google sign-in",
    )


@router.get("/me", response_model=UserPublic)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user

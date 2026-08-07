"""Auth router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.schemas.auth import LoginRequest, LoginResponse
from app.dependencies import get_current_user
from app.security.auth import AuthenticatedUser, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request, response: Response) -> LoginResponse:
    """Demo login: issues an HttpOnly session cookie."""
    container = request.app.state.container
    settings = container.settings

    row = await container.db.fetchrow(
        "SELECT user_id, email, role, customer_id, hashed_password FROM app_users WHERE email = $1 AND is_active = TRUE",
        payload.email,
    )
    if row is None or not verify_password(payload.password, row["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = AuthenticatedUser(
        user_id=row["user_id"], email=row["email"], role=row["role"], customer_id=row["customer_id"]
    )
    token = container.auth_provider.create_session_token(user)

    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
    )

    return LoginResponse(
        user_id=str(user.user_id), email=user.email, role=user.role, customer_id=user.customer_id
    )


@router.get("/me", response_model=LoginResponse)
async def me(user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> LoginResponse:
    return LoginResponse(**user.to_dict())


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict[str, str]:
    settings = request.app.state.container.settings
    response.delete_cookie(settings.session_cookie_name)
    return {"status": "logged_out"}

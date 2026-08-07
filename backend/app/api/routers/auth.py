"""Auth router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request, response: Response) -> LoginResponse:
    """Demo login: issues an HttpOnly session cookie."""
    container = request.app.state.container
    settings = container.settings

    row = await container.db.fetchrow(
        "SELECT user_id, email, role, customer_id FROM app_users WHERE email = $1 AND is_active = TRUE",
        payload.email,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    from app.security.auth import AuthenticatedUser

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


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict[str, str]:
    settings = request.app.state.container.settings
    response.delete_cookie(settings.session_cookie_name)
    return {"status": "logged_out"}

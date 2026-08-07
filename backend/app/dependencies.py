"""FastAPI dependency providers - thin wiring layer over app.state (bootstrap container)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.security.auth import AuthenticatedUser
from app.security.rbac import AuthorizationPolicy


def get_container(request: Request):
    """Get the composed dependency container from app.state (set in bootstrap)."""
    return request.app.state.container


async def get_current_user(
    request: Request,
    thinkfive_session: Annotated[str | None, Cookie()] = None,
) -> AuthenticatedUser:
    """Resolve authenticated user from the HttpOnly session cookie."""
    if thinkfive_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    container = request.app.state.container
    try:
        return container.auth_provider.verify_session_token(thinkfive_session)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def require_role(*allowed_roles: str):
    """Dependency factory enforcing that the current user has one of the allowed roles."""

    async def _check(user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> AuthenticatedUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return user

    return _check


async def require_customer_access(
    customer_id: str,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    """Ensure the current user may access the given customer's data."""
    try:
        AuthorizationPolicy.assert_customer_access(user.role, user.customer_id, customer_id)
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return user

from fastapi import HTTPException, Request, status

from app.models import User


def get_current_user(request: Request) -> User:
    """
    Authentication integration point.

    The authentication layer must set request.state.user after
    validating the user's server-side session.

    Until that integration exists, protected routes fail closed.
    """
    user = getattr(request.state, "user", None)

    if not isinstance(user, User):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if user.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active",
        )

    return user

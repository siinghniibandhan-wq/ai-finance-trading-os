"""Shared ownership dependency for user-scoped financial and tax APIs.

Legacy clients may continue sending user_id in the query string, but it must
match the identity from the signed Bearer token. The query value never grants
access to another user's records.
"""
from fastapi import Depends, HTTPException, Query
from app.models import User
from app.routes.auth import get_current_user


def require_matching_user_id(
    user_id: int = Query(..., ge=1),
    current_user: User = Depends(get_current_user),
) -> None:
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="The requested user_id does not match the authenticated user.",
        )

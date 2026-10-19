"""GitHub token validation and user management, with NPC token support."""

import json
from dataclasses import dataclass
from typing import Optional

import httpx
from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mcpkart_backend.api.cache import get_redis
from mcpkart_backend.db.database import get_async_db
from mcpkart_backend.db.models import User

# Redis key prefix for NPC tokens (must match spawner.py)
NPC_TOKEN_KEY_PREFIX = "npc:token"


def is_npc_token(token: str) -> bool:
    """Check if token is an NPC dynamic token.

    NPC tokens start with the prefix 'npc-'.

    Args:
        token: Token string to check

    Returns:
        True if token is an NPC token, False otherwise
    """
    return token.startswith("npc-")


def parse_npc_token(token: str) -> Optional[tuple[str, str, str]]:
    """Parse NPC token into components.

    Token format: "npc-{username}:{race_id}:{secret}"
    Example: "npc-bot-racer-1:race-abc123:xYz789..."

    Args:
        token: NPC token string

    Returns:
        Tuple of (username, race_id, secret) if valid, None otherwise
    """
    if not is_npc_token(token):
        return None

    try:
        token_body = token[4:]  # Remove "npc-" prefix
        parts = token_body.split(":", 2)
        if len(parts) != 3:
            return None
        username, race_id, secret = parts
        if not username or not race_id or not secret:
            return None
        return (username, race_id, secret)
    except Exception:
        return None


async def validate_npc_token(token: str) -> Optional[tuple[str, str]]:
    """Validate NPC token secret against Redis.

    Token format: "npc-{username}:{race_id}:{secret}"

    Args:
        token: Full NPC token string

    Returns:
        Tuple of (username, race_id) if valid, None otherwise
    """
    parsed = parse_npc_token(token)
    if parsed is None:
        return None

    username, race_id, secret = parsed

    try:
        # Lookup token in Redis
        redis_client = await get_redis()
        if redis_client is None:
            # Redis not available - can't validate
            return None

        token_key = f"{NPC_TOKEN_KEY_PREFIX}:{username}:{race_id}"
        token_data = await redis_client.get(token_key)

        if not token_data:
            return None

        data = json.loads(token_data)
        if data.get("secret") != secret:
            return None

        return (username, race_id)
    except Exception:
        return None


@dataclass
class AuthenticatedUser:
    """Authenticated user context."""

    github_user_id: int
    github_username: str
    email: Optional[str]
    organizations: list[str]


async def validate_github_token(token: str) -> dict:
    """Validate GitHub token and return user info.

    Calls GitHub API to get authenticated user data and organizations.

    Args:
        token: GitHub OAuth access token

    Returns:
        Dict with id, login, email, and organizations

    Raises:
        HTTPException: If token is invalid or expired
    """
    async with httpx.AsyncClient() as client:
        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=401, detail="Invalid or expired GitHub token"
            )

        user_data = user_response.json()

        # Get organizations
        orgs_response = await client.get(
            f"https://api.github.com/users/{user_data['login']}/orgs",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        orgs = []
        if orgs_response.status_code == 200:
            orgs = [org["login"] for org in orgs_response.json()]

        return {
            "id": user_data["id"],
            "login": user_data["login"],
            "email": user_data.get("email"),
            "organizations": orgs,
        }


async def get_or_create_user(db: AsyncSession, github_data: dict) -> User:
    """Get existing user or create new one from GitHub data.

    Args:
        db: Async database session
        github_data: Dict from validate_github_token with id, login, email, organizations

    Returns:
        User record (created or updated)
    """
    result = await db.execute(
        select(User).filter(User.github_user_id == github_data["id"])
    )
    user = result.scalar_one_or_none()

    if user:
        # Update username/email/orgs in case they changed
        user.github_username = github_data["login"]
        user.email = github_data["email"]
        user.organizations = github_data["organizations"]
        await db.commit()
        await db.refresh(user)
    else:
        # Create new user
        user = User(
            github_user_id=github_data["id"],
            github_username=github_data["login"],
            email=github_data["email"],
            organizations=github_data["organizations"],
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_user(
    authorization: str = Header(..., description="Bearer token from MCP server"),
    db: AsyncSession = Depends(get_async_db),
) -> AuthenticatedUser:
    """FastAPI dependency to get authenticated user from GitHub token or NPC token.

    Supports:
    - GitHub OAuth tokens: Validated via GitHub API, stored in database
    - NPC dynamic tokens: Validated against Redis, not stored in database

    Expects header: Authorization: Bearer <token>

    Args:
        authorization: Authorization header value
        db: Async database session from dependency injection

    Returns:
        AuthenticatedUser with user details

    Raises:
        HTTPException: If authorization header is invalid or token is invalid
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid authorization header format"
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    # Handle NPC tokens (validate against Redis)
    if is_npc_token(token):
        result = await validate_npc_token(token)
        if result is None:
            raise HTTPException(status_code=401, detail="Invalid NPC token")
        username, race_id = result

        return AuthenticatedUser(
            github_user_id=0,  # Sentinel value for NPCs (GitHub IDs start at 1)
            github_username=username,
            email=None,
            organizations=[],
        )

    # Handle GitHub OAuth tokens (existing flow)
    github_data = await validate_github_token(token)

    # Get or create user in database
    user = await get_or_create_user(db, github_data)

    return AuthenticatedUser(
        github_user_id=user.github_user_id,
        github_username=user.github_username,
        email=user.email,
        organizations=list(user.organizations) if user.organizations else [],
    )

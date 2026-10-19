"""Hybrid authentication for MCP Kart with GitHub OAuth and NPC dynamic tokens."""

from fastmcp.server.auth.auth import AccessToken
from fastmcp.server.auth.providers.github import GitHubProvider
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)

NPC_TOKEN_PREFIX = "npc-"


class HybridGitHubProvider(GitHubProvider):
    """GitHub OAuth provider with NPC dynamic token support.

    Extends GitHubProvider to handle NPC tokens alongside OAuth.
    NPC tokens are passed through to the backend for validation.

    Token types:
    - GitHub OAuth tokens: Standard opaque tokens from GitHub
    - NPC tokens: Dynamic format "npc-{username}:{race_id}:{secret}"

    The "npc-" prefix enables fast detection without parsing overhead.
    Secret validation is delegated to the backend (which generates the tokens).
    """

    def __init__(self, **github_kwargs):
        """Initialize with GitHub OAuth config.

        Args:
            **github_kwargs: All GitHubProvider initialization args
        """
        super().__init__(**github_kwargs)

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify token - check NPC tokens first, then GitHub.

        Args:
            token: Token string to verify

        Returns:
            AccessToken if valid, None otherwise
        """
        # Fast path: Check if NPC token (prefix check is very fast)
        if token.startswith(NPC_TOKEN_PREFIX):
            return await self._verify_npc_token(token)

        # Delegate to parent GitHubProvider for OAuth tokens
        return await super().verify_token(token)

    async def _verify_npc_token(self, token: str) -> AccessToken | None:
        """Parse NPC token and pass through to backend for validation.

        Token format: "npc-{username}:{race_id}:{secret}"
        Example: "npc-bot-racer-1:race-abc123:xYz789..."

        Secret validation is NOT done here - the backend validates
        against Redis when it receives the request.

        Args:
            token: NPC token string

        Returns:
            AccessToken if format is valid, None otherwise
        """
        try:
            # Remove prefix
            token_body = token[len(NPC_TOKEN_PREFIX):]

            # Parse username, race_id, and secret
            parts = token_body.split(":", 2)
            if len(parts) < 2:
                logger.debug("Invalid NPC token format (need at least username:race_id)")
                return None

            username = parts[0]
            race_id = parts[1] if len(parts) >= 2 else None
            # Note: secret in parts[2] is NOT validated here - backend does that

            if not username:
                logger.debug("Invalid NPC token: empty username")
                return None

            # Return AccessToken - backend will validate the secret
            return AccessToken(
                token=token,  # Pass full token to backend
                client_id=f"npc-{username}",
                scopes=self.required_scopes or [],
                expires_at=None,  # NPC tokens expire via Redis TTL
                claims={
                    "sub": username,  # Subject (standard JWT claim)
                    "login": username,  # GitHub-style username claim
                    "npc": True,  # Flag to identify NPCs
                    "race_id": race_id,  # Race this token is scoped to
                    "token_type": "npc_dynamic",
                },
            )

        except Exception as e:
            logger.debug("NPC token parsing error: %s", e)
            return None

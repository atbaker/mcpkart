"""Hybrid authentication for MCP Kart with GitHub OAuth and NPC static tokens."""

from fastmcp.server.auth.auth import AccessToken
from fastmcp.server.auth.providers.github import GitHubProvider
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)

NPC_TOKEN_PREFIX = "npc-"


class HybridGitHubProvider(GitHubProvider):
    """GitHub OAuth provider with NPC static token support.

    Extends GitHubProvider to add static token validation for NPCs
    while preserving full OAuth functionality for human players.

    Token types:
    - GitHub OAuth tokens: Standard opaque tokens from GitHub
    - NPC tokens: Static format "npc-{username}:{secret}"

    The "npc-" prefix enables fast detection without parsing overhead.
    """

    def __init__(self, npc_tokens: dict[str, str] | None = None, **github_kwargs):
        """Initialize with NPC tokens + GitHub OAuth config.

        Args:
            npc_tokens: Dict mapping NPC usernames to secrets
            **github_kwargs: All GitHubProvider initialization args
        """
        super().__init__(**github_kwargs)
        self._npc_tokens = npc_tokens or {}

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
        """Validate static NPC token.

        Token format: "npc-{username}:{secret}"
        Example: "npc-bot-racer-1:abc123xyz789"

        Args:
            token: NPC token string

        Returns:
            AccessToken if valid, None otherwise
        """
        try:
            # Remove prefix
            token_body = token[len(NPC_TOKEN_PREFIX) :]

            # Parse username and secret
            if ":" not in token_body:
                logger.debug("Invalid NPC token format (missing colon)")
                return None

            username, secret = token_body.split(":", 1)

            # Validate against configured tokens
            expected_secret = self._npc_tokens.get(username)
            if expected_secret is None:
                logger.debug("Unknown NPC username: %s", username)
                return None

            if secret != expected_secret:
                logger.debug("Invalid NPC secret for username: %s", username)
                return None

            # Return AccessToken with NPC-specific claims
            return AccessToken(
                token=token,
                client_id=f"npc-{username}",
                scopes=self.required_scopes or [],
                expires_at=None,  # NPC tokens don't expire
                claims={
                    "sub": username,  # Subject (standard JWT claim)
                    "login": username,  # GitHub-style username claim
                    "npc": True,  # Flag to identify NPCs
                    "token_type": "npc_static",
                },
            )

        except Exception as e:
            logger.debug("NPC token validation error: %s", e)
            return None

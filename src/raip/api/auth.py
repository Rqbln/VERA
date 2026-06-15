from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)

ROLE_DS = frozenset({"data_scientist", "ml_researcher"})
ROLE_CYBER = frozenset({"secops", "legal_compliance", "risk_manager", "external_auditor"})
ROLE_COMPLIANCE = frozenset(
    {"legal_compliance", "risk_manager", "domain_expert", "external_auditor", "executive"}
)
ROLE_INSPECTOR = frozenset(
    {"secops", "legal_compliance", "external_auditor", "ml_researcher", "risk_manager"}
)
ALL_ROLES = frozenset(
    {
        "ml_researcher",
        "data_scientist",
        "secops",
        "domain_expert",
        "external_auditor",
        "legal_compliance",
        "risk_manager",
        "executive",
    }
)


@dataclass
class AuthUser:
    sub: str
    roles: frozenset[str]
    raw: dict[str, Any]


_jwks_cache: dict[str, Any] | None = None


def auth_disabled() -> bool:
    return os.environ.get("RAIP_AUTH_DISABLED", "").lower() in ("1", "true", "yes")


def keycloak_issuer() -> str:
    base = os.environ.get("KEYCLOAK_URL", "http://localhost:8080").rstrip("/")
    realm = os.environ.get("KEYCLOAK_REALM", "raip")
    return f"{base}/realms/{realm}"


def _dev_user() -> AuthUser:
    roles = os.environ.get("RAIP_DEV_ROLES", "legal_compliance,ml_researcher").split(",")
    return AuthUser(sub="dev-user", roles=frozenset(r.strip() for r in roles if r.strip()), raw={})


async def _fetch_jwks() -> dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    url = f"{keycloak_issuer()}/protocol/openid-connect/certs"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        return _jwks_cache


def _roles_from_claims(claims: dict[str, Any]) -> frozenset[str]:
    realm_access = claims.get("realm_access") or {}
    roles = set(realm_access.get("roles") or [])
    resource_access = claims.get("resource_access") or {}
    for client_roles in resource_access.values():
        if isinstance(client_roles, dict):
            roles.update(client_roles.get("roles") or [])
    return frozenset(r for r in roles if r in ALL_ROLES)


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthUser:
    if auth_disabled():
        return _dev_user()
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        import jwt
        from jwt import PyJWKClient
    except ImportError as e:
        raise HTTPException(status_code=500, detail="PyJWT not installed") from e

    issuer = keycloak_issuer()
    jwks_url = f"{issuer}/protocol/openid-connect/certs"
    try:
        jwk_client = PyJWKClient(jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(creds.credentials)
        decode_opts: dict[str, Any] = {"verify_aud": False}
        claims = jwt.decode(
            creds.credentials,
            signing_key.key,
            algorithms=["RS256"],
            options=decode_opts,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}") from e

    roles = _roles_from_claims(claims)
    if not roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No RAIP roles assigned")
    return AuthUser(sub=str(claims.get("sub", "")), roles=roles, raw=claims)


def require_roles(*allowed: str):
    allowed_set = frozenset(allowed)

    async def _dep(user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
        if auth_disabled():
            return user
        if not user.roles.intersection(allowed_set):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _dep

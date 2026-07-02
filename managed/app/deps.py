"""FastAPI dependencies: DB session, collector auth, admin auth."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, params, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.client_tokens import hash_token
from app.auth.oidc import InvalidAdminTokenError, OIDCNotConfiguredError, OIDCVerifier
from app.auth.rbac import AdminPrincipal, Role
from app.config import Settings
from app.db.models import CollectorToken, Organization

bearer_scheme = HTTPBearer(auto_error=False)


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_db(request: Request) -> Iterator[Session]:
    session: Session = request.app.state.session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


DbDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_collector_organization(
    credentials: CredentialsDep,
    db: DbDep,
    settings: SettingsDep,
) -> Organization:
    if settings.collector_token_pepper is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="collector token pepper is not configured",
        )
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="collector token required")
    digest = hash_token(settings.collector_token_pepper, credentials.credentials)
    token = db.scalars(
        select(CollectorToken).where(CollectorToken.token_hash == digest, CollectorToken.active.is_(True))
    ).first()
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid collector token")
    return token.organization


CollectorOrgDep = Annotated[Organization, Depends(get_collector_organization)]


def get_admin_principal(request: Request, credentials: CredentialsDep) -> AdminPrincipal:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin bearer token required")
    verifier: OIDCVerifier = request.app.state.oidc_verifier
    try:
        return verifier.verify(credentials.credentials)
    except OIDCNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin OIDC is not configured",
        ) from exc
    except InvalidAdminTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid admin token") from exc


AdminPrincipalDep = Annotated[AdminPrincipal, Depends(get_admin_principal)]


def get_admin_organization(principal: AdminPrincipalDep, db: DbDep) -> Organization:
    organization = db.scalars(select(Organization).where(Organization.key == principal.organization_key)).first()
    if organization is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="unknown organization")
    return organization


AdminOrgDep = Annotated[Organization, Depends(get_admin_organization)]


def require_roles(*allowed: Role) -> params.Depends:
    def check(principal: AdminPrincipalDep) -> AdminPrincipal:
        if not principal.has_any(allowed):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")
        return principal

    return Depends(check)

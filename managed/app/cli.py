"""Operator CLI for bootstrap tasks that have no API surface yet.

Runs inside the api container (``python -m app.cli ...``), against the same
environment configuration. Creating a collector token prints the raw token
exactly once; only its hash is stored.
"""

import argparse
import sys
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.client_tokens import generate_token, hash_token
from app.config import Settings, get_settings
from app.db.models import CollectorToken, Organization
from app.db.session import build_engine, build_session_factory


def create_org(db: Session, key: str, name: str) -> Organization:
    existing = db.scalars(select(Organization).where(Organization.key == key)).first()
    if existing is not None:
        raise SystemExit(f"organization '{key}' already exists")
    organization = Organization(key=key, name=name)
    db.add(organization)
    db.flush()
    return organization


def create_collector_token(db: Session, settings: Settings, org_key: str, name: str) -> str:
    if settings.collector_token_pepper is None:
        raise SystemExit("CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER is not set")
    organization = db.scalars(select(Organization).where(Organization.key == org_key)).first()
    if organization is None:
        raise SystemExit(f"organization '{org_key}' not found")
    raw = generate_token()
    db.add(
        CollectorToken(
            organization_id=organization.id,
            name=name,
            token_hash=hash_token(settings.collector_token_pepper, raw),
        )
    )
    db.flush()
    return raw


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description="Managed server operator commands.")
    sub = parser.add_subparsers(dest="command", required=True)

    org = sub.add_parser("create-org", help="Create an organization.")
    org.add_argument("--key", required=True)
    org.add_argument("--name", required=True)

    token = sub.add_parser("create-token", help="Mint a collector token (raw value printed once).")
    token.add_argument("--org-key", required=True)
    token.add_argument("--name", required=True)

    args = parser.parse_args(argv)
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    with session_factory() as db:
        if args.command == "create-org":
            organization = create_org(db, args.key, args.name)
            db.commit()
            sys.stdout.write(f"created organization {organization.key} ({organization.id})\n")
        else:
            raw = create_collector_token(db, settings, args.org_key, args.name)
            db.commit()
            sys.stdout.write(f"{raw}\n")
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

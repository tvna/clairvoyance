"""Operator CLI: org creation and one-time token minting."""

from pathlib import Path

import pytest
from conftest import TEST_PEPPER, make_settings
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.cli as cli_module
from app.auth.client_tokens import hash_token
from app.cli import create_collector_token, create_org, main
from app.db.base import Base
from app.db.models import CollectorToken
from app.db.session import build_engine


def test_create_org_rejects_duplicate_key(db: Session) -> None:
    create_org(db, "acme", "Acme")
    with pytest.raises(SystemExit, match="already exists"):
        create_org(db, "acme", "Acme Again")


def test_create_token_requires_pepper(db: Session) -> None:
    with pytest.raises(SystemExit, match="PEPPER"):
        create_collector_token(db, make_settings(collector_token_pepper=None), "acme", "t")


def test_create_token_requires_org(db: Session) -> None:
    with pytest.raises(SystemExit, match="not found"):
        create_collector_token(db, make_settings(), "ghost", "t")


def test_create_token_stores_hash_only(db: Session) -> None:
    create_org(db, "acme", "Acme")
    raw = create_collector_token(db, make_settings(), "acme", "ci")
    stored = db.scalars(select(CollectorToken)).one()
    assert raw.startswith("cvk_")
    assert raw not in stored.token_hash
    assert stored.token_hash == hash_token(TEST_PEPPER, raw)


def test_main_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    settings = make_settings(database_url=f"sqlite:///{tmp_path}/cli.db")
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    engine.dispose()
    monkeypatch.setattr(cli_module, "get_settings", lambda: settings)

    assert main(["create-org", "--key", "acme", "--name", "Acme"]) == 0
    assert "created organization acme" in capsys.readouterr().out

    assert main(["create-token", "--org-key", "acme", "--name", "ci"]) == 0
    token_line = capsys.readouterr().out.strip()
    assert token_line.startswith("cvk_")

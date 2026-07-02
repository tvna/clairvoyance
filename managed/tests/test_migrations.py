"""Migration smoke test: the initial revision applies and reverts cleanly."""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

MANAGED_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {
    "organizations",
    "collector_tokens",
    "contributors",
    "coaching_events",
    "quiz_attempts",
    "review_schedules",
    "admin_policies",
    "audit_logs",
}


def run_alembic(database_url: str, *args: str) -> None:
    env = os.environ.copy()
    env["CLAIRVOYANCE_DATABASE_URL"] = database_url
    env.setdefault("CLAIRVOYANCE_REDIS_URL", "redis://127.0.0.1:6399/0")
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=MANAGED_ROOT,
        env=env,
        check=True,
        capture_output=True,
    )


def test_upgrade_and_downgrade(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path}/migrate.db"
    run_alembic(database_url, "upgrade", "head")

    engine = create_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    assert tables >= EXPECTED_TABLES

    run_alembic(database_url, "downgrade", "base")
    engine = create_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    assert not (EXPECTED_TABLES & tables)

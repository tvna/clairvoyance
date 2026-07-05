"""Migration smoke test: the initial revision applies and reverts cleanly,
via the same console-script entry point the container uses, and the migrated
schema structurally matches the models (drift gate)."""

import os
import subprocess
import sys
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.db.base import Base

MANAGED_ROOT = Path(__file__).resolve().parents[1]
# The console script, not `python -m alembic`: the container invokes the
# script, which (unlike -m) does not put the cwd on sys.path — this is what
# alembic.ini's prepend_sys_path covers, so exercise that exact path.
ALEMBIC = Path(sys.executable).parent / "alembic"

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
        [str(ALEMBIC), *args],
        cwd=MANAGED_ROOT,
        env=env,
        check=True,
        capture_output=True,
    )


def test_upgrade_matches_models_and_downgrades(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path}/migrate.db"
    run_alembic(database_url, "upgrade", "head")

    engine = create_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    assert tables >= EXPECTED_TABLES

    # Drift gate: a model change without a matching migration must fail here,
    # because the app tests build schema via create_all and would stay green.
    # Scope is structural (tables/columns); type-level comparison is skipped —
    # SQLite reflection reports generic affinities that false-positive on it.
    with engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": False})
        diff = compare_metadata(context, Base.metadata)
    structural = [d for d in diff if d[0] in ("add_table", "remove_table", "add_column", "remove_column")]
    assert structural == []
    engine.dispose()

    run_alembic(database_url, "downgrade", "base")
    engine = create_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    assert not (EXPECTED_TABLES & tables)

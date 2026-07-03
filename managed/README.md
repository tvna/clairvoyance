# Managed Coaching Server

Server-side foundation for **managed mode**: organizations run this service so
coaches and admins can see coaching state across contributors, while local
modes (`off` / `lite` / `sqlite`) keep working unchanged on the workstation.
Tracking issue: #51 (follow-up to #34).

Local clients never talk to the database directly. Everything goes through the
API server, which owns authentication, idempotency, policy, and audit.

```mermaid
flowchart LR
    C["Local Client / Skill"] --> A["FastAPI Collector API"]
    A --> P["PostgreSQL"]
    A --> R["Redis"]
    W["Celery Worker"] --> P
    W --> R
    Admin["Admin User"] --> SPA["Admin UI (own image, ui/)"]
    SPA -- "Bearer" --> AdminAPI["Admin API"]
    AdminAPI --> P
```

## Stack

FastAPI + Pydantic v2, SQLAlchemy 2 + Alembic on PostgreSQL (psycopg), Celery
on Redis, packaged with uv into one container image that runs as `api`,
`worker`, `scheduler`, or `migrate` depending on the command (Coolify Compose
today, Deployment / CronJob / Job on Kubernetes later).

## Design decisions vs. the original draft

The first design draft was revised in these places (rationale in #51):

1. **Single ingestion path.** `POST /v1/events` carries observations, session
   markers, and quiz attempts, discriminated by `event_type`. The draft's
   separate `POST /v1/sessions` and `POST /v1/quiz-attempts` endpoints were
   dropped: one contract, one idempotency mechanism, one schema version.
2. **Explicit idempotency semantics.** `(organization_id, event_id)` is
   unique. Replaying the same body returns `200 {duplicate: true}` carrying
   the same facts as the original acknowledgement (`context_summary_stored`,
   `review_due_at`); the same `event_id` with a different body is `409` — an
   event is never overwritten. Unique constraints backstop the pre-checks
   against concurrent inserts (both the event and a first-seen contributor),
   and the redundant `organization_key` field is excluded from the body hash
   so adding/dropping it on a retry is not a conflict.
3. **`quiz_attempts` has a real FK.** The draft's dangling `event_id` became
   `event_pk -> coaching_events.id` (one attempt per event, `ON DELETE
   CASCADE` so retention cleanup stays consistent).
4. **`context_summary` is default-deny.** Stored only when the organization
   policy sets `allow_context_summary: true`, and the response always states
   `context_summary_stored` so a policy strip is never a silent drop.
5. **`contributors.email` is optional.** Identity is `provider + external_id`
   within the organization; display name and email are refreshed attributes.
6. **Teams are deferred.** The draft had `/v1/admin/teams/{id}/trends` but no
   `teams` table; no dead `team_id` column ships until teams are modeled.
7. **Admin writes are audited too**, not just reads — and the audit is
   router-level, not per-handler copy-paste: every admin route (including
   404 probes and role-denied attempts) appends to `audit_logs` with the
   route name as the action, via a dependency with its own committed
   session, so a new endpoint cannot forget the trail and a handler
   rollback cannot erase it.
8. **Retention has a default and an enforcement point**: `retention_days`
   (default 365) per organization policy, enforced daily by the Celery beat
   task against `occurred_at` (so imported history does not outlive the
   policy by a fresh ingestion window); deleted events take their quiz
   attempts along via FK cascade. `CLAIRVOYANCE_RETENTION_DRY_RUN=true`
   makes the job report counts without deleting — run one verification pass
   before enabling a tighter policy.
9. **Review spacing follows the skill-side contract** (`quiz.md`): 1 day for
   an overconfident miss, 2 for other misses, 3/5/7 days for correct with
   low/medium/high confidence, measured from `occurred_at`; an out-of-order
   older attempt never overwrites the schedule a newer one produced.

Value vocabularies (category, outcome, confidence, calibration) match the
local adaptive store (`skills/adaptive-coaching/references/store.md`), so a
later local-to-managed import does not re-encode history. Evidence levels are
`observed | imported | inferred | missing`; full backcasting is explicitly out
of scope — unrecorded confidence/calibration is never reconstructed.

## API surface

Collector (bearer collector token, org-scoped):

- `POST /v1/events` — idempotent ingestion (see semantics above)
- `GET /v1/client/policy` — what the org allows the client to collect

Admin (OIDC bearer, RBAC: `org_admin`, `team_manager`, `coach`, `auditor`):

- `GET /v1/admin/contributors`
- `GET /v1/admin/contributors/{id}/summary`
- `GET /v1/admin/reviews/due`
- `GET /v1/admin/policies` / `PUT /v1/admin/policies` (org_admin only)
- `GET /v1/admin/audit-logs` (org_admin, auditor)

Probes: `GET /healthz`, `GET /livez` (liveness), `GET /readyz` (DB + Redis).

## Authentication

- **Collector**: organization-scoped tokens minted by
  `python -m app.cli create-token`. Only `HMAC-SHA256(pepper, token)` is
  stored; the raw token prints once and is never persisted or logged. The
  pepper is `CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER` (api process only).
- **Admin**: OIDC bearer JWTs verified against the issuer's JWKS
  (`RS256`/`ES256`, `iss`/`aud`/`exp` required). Provider-agnostic; the
  organization key and roles ride in claims (`CLAIRVOYANCE_OIDC_ORG_CLAIM`,
  `CLAIRVOYANCE_OIDC_ROLES_CLAIM`, defaults `org` / `roles`). The JWKS URL
  (`CLAIRVOYANCE_OIDC_JWKS_URL`) is explicit — providers publish it at
  different paths, so the server never guesses it from the issuer.
  Unconfigured OIDC and JWKS fetch failures fail loudly with 503 (never
  open, and never disguised as a 401 credential error).

## Configuration

`CLAIRVOYANCE_`-prefixed environment variables (Kubernetes-ready: config via
env, stateless app): `DATABASE_URL`, `REDIS_URL`, `COLLECTOR_TOKEN_PEPPER`,
`OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`, `OIDC_ROLES_CLAIM`,
`OIDC_ORG_CLAIM`, `RETENTION_DRY_RUN`.

When a real deployment mints these secrets: generate the pepper locally
(`python -c "import secrets; print(secrets.token_urlsafe(48))"`), store it as
a Coolify runtime environment secret scoped to the `api` service, and verify
the handoff by minting a token with `app.cli create-token` and calling
`GET /v1/client/policy` with it. Rotating the pepper invalidates every
collector token; rotate by re-minting tokens, not by editing hashes.

## Development

```bash
cd managed
uv sync
uv run ruff check && uv run ruff format --check
uv run mypy
uv run pytest        # 100% coverage gate, SQLite-backed, no services needed
```

Local smoke test against real Postgres/Redis:

```bash
export CLAIRVOYANCE_DATABASE_URL=postgresql+psycopg://user:pass@localhost/clairvoyance
export CLAIRVOYANCE_REDIS_URL=redis://localhost:6379/0
export CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
uv run alembic upgrade head
uv run python -m app.cli create-org --key acme --name "Acme"
uv run python -m app.cli create-token --org-key acme --name dev
uv run uvicorn app.main:create_app --factory --reload
```

## Admin UI

`ui/` is the admin frontend (React + TypeScript + Vite SPA), its own npm
project shipping as its own image — see
[docs/frontend-design.md](docs/frontend-design.md) for the design and
[ui/README.md](ui/README.md) for development. The api process, its schemas,
and its routes are unchanged by the UI's existence.

## Deployment (Coolify)

`docker-compose.coolify.yml` runs `api` (public domain, health-checked),
`worker`, `scheduler`, and `ui` from two images (api/worker/scheduler share
one, ui is separate). Postgres and Redis are Coolify database resources on
the internal network — not bundled in the Compose file — so Coolify owns
their lifecycle and backups (S3-compatible storage). Migration runs in the
api command before uvicorn starts; with a single api instance that is
race-free. When replicas scale out (or on Kubernetes), move
`alembic upgrade head` into a one-shot service / Job.

`api` and `ui` share one public domain, split by path at the edge router
(Traefik under Coolify): `/ui/*` -> ui, everything else -> api. The claim-name
variables (`CLAIRVOYANCE_OIDC_ROLES_CLAIM` / `CLAIRVOYANCE_OIDC_ORG_CLAIM`)
must be set once from a shared source (a Coolify shared variable) and bound
to both services — if they drift, the UI shapes navigation from claims the
server does not verify. `CLAIRVOYANCE_OIDC_CLIENT_ID` is ui-only (the public
OIDC client the SPA authenticates as); the api service needs no client
identifier of its own.

Registering the SPA with the OIDC provider: create a public client (no
client secret), redirect URI `https://<domain>/ui/callback`, post-logout
redirect URI `https://<domain>/ui/`, refresh-token rotation enabled for the
public client. Verify the deployment by signing in, loading
`/ui/contributors`, and confirming sign-out actually ends the session (reload
must require credentials again) — a provider with no end-session endpoint
will not end the session on sign-out and the UI says so.

Kubernetes mapping when the time comes: `api` -> Deployment + Service +
Ingress, `worker` -> Deployment, `scheduler` -> CronJob or beat Deployment,
`ui` -> Deployment + Service (same Ingress, path-routed), env vars ->
ConfigMap/Secret, health checks -> probes, migrate -> Job.

## Deferred (tracked in #51)

- Teams model and team trend endpoints.
- Collector rate limiting (needs a limits decision).
- Local-mode history import tooling (`evidence_level: imported`).
- Admin UI API gaps recorded in
  [docs/frontend-design.md §14](docs/frontend-design.md#14-api-gaps-observed-follow-ups-none-blocking-v1)
  (contributor search, reviews-due pagination/identity, review dismissal,
  audit-log filters) — none blocking the UI's v1.

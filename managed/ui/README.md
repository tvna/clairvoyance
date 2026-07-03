# Admin UI

React + TypeScript + Vite SPA for the managed coaching server's admin API.
Design: [`../docs/frontend-design.md`](../docs/frontend-design.md). Ships as
its own image, independent from `managed/` (the api/worker/scheduler image) —
see that design doc's §3 for why.

## Development

```bash
cd managed/ui
npm ci
npm run dev
```

The dev server expects `/ui/config.json` to exist (fetched at boot — see
design §6). For local UI-only iteration without a running admin API, serve a
static one from `public/` or intercept the request in devtools; for a real
end-to-end loop use the E2E compose in `e2e/` (below).

## Quality gates

```bash
npx biome ci .
npx tsc --noEmit
npx vitest run
npm run build
```

All four must pass — this is the `managed-ui` CI job.

## E2E smoke

```bash
cd e2e
docker compose -f docker-compose.e2e.yml up -d --build --wait
docker compose -f docker-compose.e2e.yml exec -T api \
  python -m app.cli create-org --key acme --name "Local E2E"
cd ..
npx playwright test e2e/
docker compose -f e2e/docker-compose.e2e.yml down -v
```

This composes the ui image, the api image, Postgres, Redis, a front proxy
doing the same `/ui`-vs-API path split the production edge does, and a
purpose-built stub OIDC issuer (`e2e/stub-issuer/`, a standalone Python
service — see its module docstring). This is the `managed-ui-e2e` CI job.

## Image

`Dockerfile`: a node build stage, then an nginx final stage whose entrypoint
(`server/entrypoint.sh`) renders `/ui/config.json` and the nginx vhost from
environment at container start (design §6/§11), failing loudly before nginx
starts if a required variable is missing.

Required: `CLAIRVOYANCE_OIDC_ISSUER`, `CLAIRVOYANCE_OIDC_CLIENT_ID`,
`CLAIRVOYANCE_OIDC_AUDIENCE`. Optional:
`CLAIRVOYANCE_OIDC_ROLES_CLAIM`/`CLAIRVOYANCE_OIDC_ORG_CLAIM` (default
`roles`/`org`, matching the api service's own defaults) and
`CLAIRVOYANCE_OIDC_AUTHORIZE_URL`/`CLAIRVOYANCE_OIDC_TOKEN_URL`/
`CLAIRVOYANCE_OIDC_END_SESSION_URL` (unset by default; only needed when the
provider's discovery document is absent or non-standard).

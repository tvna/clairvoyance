#!/bin/sh
# Renders /ui/config.json and the nginx vhost from environment at container
# start (design §6/§11). Fails loud before nginx starts when a required
# variable is missing -- no user should see a broken sign-in.
set -eu

require_var() {
  var_name="$1"
  eval "value=\${$var_name:-}"
  if [ -z "$value" ]; then
    echo "entrypoint: required environment variable $var_name is not set" >&2
    exit 1
  fi
}

require_var CLAIRVOYANCE_OIDC_ISSUER
require_var CLAIRVOYANCE_OIDC_CLIENT_ID
require_var CLAIRVOYANCE_OIDC_AUDIENCE

# Same defaults as the api service's own claim-name settings
# (app/config.py), so a deployment that never touches these stays
# consistent between the two images out of the box.
ORG_CLAIM="${CLAIRVOYANCE_OIDC_ORG_CLAIM:-org}"
ROLES_CLAIM="${CLAIRVOYANCE_OIDC_ROLES_CLAIM:-roles}"

# The only characters these values (URLs, claim names) could plausibly
# carry that would break the JSON string are backslash and double-quote.
json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

CONFIG_JSON_PATH=/usr/share/nginx/html/ui/config.json
{
  printf '{'
  printf '"issuer":"%s",' "$(json_escape "$CLAIRVOYANCE_OIDC_ISSUER")"
  printf '"client_id":"%s",' "$(json_escape "$CLAIRVOYANCE_OIDC_CLIENT_ID")"
  printf '"audience":"%s",' "$(json_escape "$CLAIRVOYANCE_OIDC_AUDIENCE")"
  printf '"org_claim":"%s",' "$(json_escape "$ORG_CLAIM")"
  printf '"roles_claim":"%s"' "$(json_escape "$ROLES_CLAIM")"
  # Optional endpoint overrides (design §6): omitted entirely, not emitted
  # as empty strings, when unset -- the SPA falls back to issuer discovery.
  if [ -n "${CLAIRVOYANCE_OIDC_AUTHORIZE_URL:-}" ]; then
    printf ',"authorization_endpoint":"%s"' "$(json_escape "$CLAIRVOYANCE_OIDC_AUTHORIZE_URL")"
  fi
  if [ -n "${CLAIRVOYANCE_OIDC_TOKEN_URL:-}" ]; then
    printf ',"token_endpoint":"%s"' "$(json_escape "$CLAIRVOYANCE_OIDC_TOKEN_URL")"
  fi
  if [ -n "${CLAIRVOYANCE_OIDC_END_SESSION_URL:-}" ]; then
    printf ',"end_session_endpoint":"%s"' "$(json_escape "$CLAIRVOYANCE_OIDC_END_SESSION_URL")"
  fi
  printf '}\n'
} > "$CONFIG_JSON_PATH"

# CSP connect-src needs the issuer's origin, not the full issuer URL
# (design §9).
ISSUER_ORIGIN=$(printf '%s' "$CLAIRVOYANCE_OIDC_ISSUER" | sed -E 's#^(https?://[^/]+).*#\1#')
export ISSUER_ORIGIN

# Restricted to just this one variable: nginx's own config syntax uses
# `$` for its variables too ($host, $uri, ...), and an unrestricted
# envsubst would blank all of those out.
envsubst '${ISSUER_ORIGIN}' < /etc/nginx/templates/security-headers.conf.template > /etc/nginx/conf.d/security-headers.conf
envsubst '${ISSUER_ORIGIN}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec "$@"

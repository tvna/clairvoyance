"""Admin roles and the principal extracted from a verified OIDC token."""

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ORG_ADMIN = "org_admin"
    TEAM_MANAGER = "team_manager"
    COACH = "coach"
    AUDITOR = "auditor"


# Read access to coaching data (contributors, summaries, reviews, policies).
READ_ROLES = (Role.ORG_ADMIN, Role.TEAM_MANAGER, Role.COACH, Role.AUDITOR)
# Policy changes are an org_admin decision.
POLICY_WRITE_ROLES = (Role.ORG_ADMIN,)
# Dismissing a review is a coaching action: wider than policy writes (a coach
# clears the queue for a departed contributor), narrower than plain reads.
REVIEW_DISMISS_ROLES = (Role.ORG_ADMIN, Role.COACH)
# The audit trail itself is restricted to admin and auditor.
AUDIT_READ_ROLES = (Role.ORG_ADMIN, Role.AUDITOR)


@dataclass(frozen=True)
class AdminPrincipal:
    subject: str
    organization_key: str
    roles: frozenset[Role]

    def has_any(self, allowed: tuple[Role, ...]) -> bool:
        return bool(self.roles.intersection(allowed))


def parse_roles(raw: object) -> frozenset[Role]:
    """Map the roles claim to known roles, ignoring foreign entries."""
    if not isinstance(raw, list):
        return frozenset()
    known = {role.value: role for role in Role}
    return frozenset(known[item] for item in raw if isinstance(item, str) and item in known)

import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { AUDIT_READ_ROLES, hasAnyRole, type Role } from "../auth/roles";
import styles from "./Layout.module.css";

interface NavItem {
  to: string;
  label: string;
  end?: boolean;
  requiredRoles: readonly Role[] | null;
}

// Design §2's capability table. Hiding an item here is a courtesy only —
// the server still enforces and audits role-denied direct navigation
// (see ForbiddenView/QueryBoundary), so this list is not a security
// control.
const NAV_ITEMS: readonly NavItem[] = [
  { to: "/", label: "Contributors", end: true, requiredRoles: null },
  { to: "/reviews", label: "Reviews due", requiredRoles: null },
  { to: "/policies", label: "Policies", requiredRoles: null },
  { to: "/audit", label: "Audit logs", requiredRoles: AUDIT_READ_ROLES },
];

export function Layout() {
  const { principal, signOut, signOutNotice } = useAuth();

  if (principal === null) {
    // RequireAuth guarantees a principal by the time Layout renders.
    return null;
  }

  return (
    <div className={styles.shell}>
      {signOutNotice !== null && (
        <div className={styles.notice} role="status">
          {signOutNotice}
        </div>
      )}
      <header className={styles.topbar}>
        <span className={styles.orgKey}>{principal.organizationKey}</span>
        <span>{principal.subject}</span>
        <span className={styles.roles}>{Array.from(principal.roles).join(", ") || "no roles"}</span>
        <span className={styles.spacer} />
        <button type="button" onClick={() => void signOut()}>
          Sign out
        </button>
      </header>
      <div className={styles.body}>
        <nav className={styles.nav}>
          <ul>
            {NAV_ITEMS.filter(
              (item) =>
                item.requiredRoles === null || hasAnyRole(principal.roles, item.requiredRoles),
            ).map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} end={item.end ?? false}>
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

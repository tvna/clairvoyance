import styles from "./ForbiddenView.module.css";

/**
 * Design §8/§2: hiding a nav item is a courtesy, not a control. A
 * hand-crafted request to a role-denied route still gets 403 from the
 * server (and lands in the audit trail); this view names the missing
 * capability rather than silently redirecting away.
 */
export function ForbiddenView({ capability }: { capability: string }) {
  return (
    <div className={styles.state} role="alert">
      <h2>Access denied</h2>
      <p>Your roles do not allow you to {capability}.</p>
    </div>
  );
}

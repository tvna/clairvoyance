import styles from "./Pagination.module.css";

/**
 * Offset pagination. `totalLabel` is only passed by screens whose
 * endpoint carries a `total` (Contributors) — Audit logs has none by
 * design (§7.5) and passes no label rather than a wrong count.
 */
export function Pagination({
  offset,
  limit,
  hasNextPage,
  totalLabel,
  onOffsetChange,
}: {
  offset: number;
  limit: number;
  hasNextPage: boolean;
  totalLabel?: string;
  onOffsetChange: (nextOffset: number) => void;
}) {
  return (
    <div className={styles.bar}>
      <button
        type="button"
        disabled={offset === 0}
        onClick={() => onOffsetChange(Math.max(0, offset - limit))}
      >
        Previous
      </button>
      <button type="button" disabled={!hasNextPage} onClick={() => onOffsetChange(offset + limit)}>
        Next
      </button>
      {totalLabel !== undefined && <span className={styles.label}>{totalLabel}</span>}
    </div>
  );
}

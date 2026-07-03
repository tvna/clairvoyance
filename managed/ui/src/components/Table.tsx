import type { ReactNode } from "react";
import styles from "./Table.module.css";

export interface TableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

/**
 * A real `<table>` (design §10: keyboard-reachable, not a div grid). Row
 * navigation (e.g. Contributors → summary) is a `<Link>` inside a cell
 * rather than a row-level click handler, so it stays keyboard-reachable
 * without extra ARIA wiring.
 */
export function Table<T>({
  columns,
  rows,
  getRowKey,
  emptyState,
  caption,
}: {
  columns: readonly TableColumn<T>[];
  rows: readonly T[];
  getRowKey: (row: T, index: number) => string;
  emptyState?: ReactNode;
  caption?: string;
}) {
  if (rows.length === 0) {
    return <div className={styles.empty}>{emptyState ?? "No rows."}</div>;
  }
  return (
    <table className={styles.table}>
      {caption !== undefined && <caption>{caption}</caption>}
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} scope="col">
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={getRowKey(row, index)}>
            {columns.map((column) => (
              <td key={column.key}>{column.render(row)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

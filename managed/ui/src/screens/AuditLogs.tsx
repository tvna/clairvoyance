import { useState } from "react";
import { useAuditLogs } from "../api/queries";
import type { AuditLogOut } from "../api/schemas";
import { DateCell } from "../components/DateCell";
import { Pagination } from "../components/Pagination";
import { QueryBoundary } from "../components/QueryBoundary";
import { Table, type TableColumn } from "../components/Table";

const PAGE_SIZE = 50;

const COLUMNS: readonly TableColumn<AuditLogOut>[] = [
  { key: "created_at", header: "When", render: (row) => <DateCell value={row.created_at} /> },
  { key: "actor", header: "Actor", render: (row) => row.actor },
  { key: "action", header: "Action", render: (row) => row.action },
  {
    key: "target",
    header: "Target",
    render: (row) => (row.target_type !== null ? `${row.target_type}:${row.target_id ?? ""}` : ""),
  },
];

export function AuditLogs() {
  const [offset, setOffset] = useState(0);
  const query = useAuditLogs(PAGE_SIZE, offset);

  return (
    <section>
      <h1>Audit logs</h1>
      <p role="status">Viewing this screen writes an audit row of its own.</p>
      <QueryBoundary query={query} capability="view audit logs">
        {(data) => (
          <>
            <Table
              columns={COLUMNS}
              rows={data.logs}
              getRowKey={(row, index) => `${offset}-${index}-${row.created_at}`}
              emptyState={<p>No audit activity yet.</p>}
            />
            {/* The endpoint now carries `total` (design §14 gap 3), so paging
                is total-driven and shows the count, like Contributors. */}
            <Pagination
              offset={offset}
              limit={PAGE_SIZE}
              hasNextPage={offset + PAGE_SIZE < data.total}
              totalLabel={`${data.total} total`}
              onOffsetChange={setOffset}
            />
          </>
        )}
      </QueryBoundary>
    </section>
  );
}

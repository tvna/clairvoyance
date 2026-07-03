import { Link } from "react-router-dom";
import { useCachedContributorLookup, useReviewsDue } from "../api/queries";
import type { ReviewDueOut } from "../api/schemas";
import { humanizeCategory } from "../api/vocabulary";
import { DateCell } from "../components/DateCell";
import { QueryBoundary } from "../components/QueryBoundary";
import { Table, type TableColumn } from "../components/Table";
import { displayName } from "./Contributors";

const PAGE_SIZE = 50;
const DAY_MS = 24 * 60 * 60 * 1000;

function overdueLabel(dueAt: string): string {
  const days = Math.floor((Date.now() - new Date(dueAt).getTime()) / DAY_MS);
  if (days <= 0) {
    return "Due today";
  }
  return `Overdue by ${days} day${days === 1 ? "" : "s"}`;
}

export function ReviewsDue() {
  const query = useReviewsDue(PAGE_SIZE);
  // Client-side join against whatever contributor list pages are already
  // cached (design §7.3) — deliberately not a fetch, so this queue never
  // triggers per-row audited aggregate calls.
  const contributorLookup = useCachedContributorLookup();

  const columns: readonly TableColumn<ReviewDueOut>[] = [
    {
      key: "due_at",
      header: "Due",
      render: (row) => (
        <>
          <DateCell value={row.due_at} /> — {overdueLabel(row.due_at)}
        </>
      ),
    },
    { key: "category", header: "Category", render: (row) => humanizeCategory(row.category) },
    { key: "signal", header: "Signal", render: (row) => row.signal ?? "" },
    { key: "interval_days", header: "Interval (days)", render: (row) => row.interval_days },
    { key: "last_outcome", header: "Last outcome", render: (row) => row.last_outcome ?? "" },
    {
      key: "contributor",
      header: "Contributor",
      render: (row) => {
        const contributor = contributorLookup.get(row.contributor_id);
        const label =
          contributor !== undefined
            ? displayName(contributor)
            : `${row.contributor_id.slice(0, 8)}…`;
        return <Link to={`/contributors/${row.contributor_id}`}>{label}</Link>;
      },
    },
  ];

  return (
    <section>
      <h1>Reviews due</h1>
      <QueryBoundary query={query} capability="view reviews due">
        {(data) => (
          <>
            <Table
              columns={columns}
              rows={data.due}
              getRowKey={(row, index) => `${row.contributor_id}-${row.category}-${index}`}
              emptyState={<p>No reviews due.</p>}
            />
            <p>
              This queue is read-only: schedules move when the contributor's next quiz attempt is
              ingested. There is no "mark reviewed" action in this release.
            </p>
          </>
        )}
      </QueryBoundary>
    </section>
  );
}

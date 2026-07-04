import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useDismissReview, useReviewsDue } from "../api/queries";
import type { ReviewDueOut } from "../api/schemas";
import { humanizeCategory } from "../api/vocabulary";
import { useAuth } from "../auth/AuthContext";
import { hasAnyRole, REVIEW_DISMISS_ROLES } from "../auth/roles";
import { DateCell } from "../components/DateCell";
import { ErrorState } from "../components/ErrorState";
import { QueryBoundary } from "../components/QueryBoundary";
import { Table, type TableColumn } from "../components/Table";

const PAGE_SIZE = 50;
const DAY_MS = 24 * 60 * 60 * 1000;

function overdueLabel(dueAt: string): string {
  const days = Math.floor((Date.now() - new Date(dueAt).getTime()) / DAY_MS);
  if (days <= 0) {
    return "Due today";
  }
  return `Overdue by ${days} day${days === 1 ? "" : "s"}`;
}

function rowLabel(row: ReviewDueOut): string {
  // Identity now rides on the row (design §7.3): no client-side join.
  return row.display_name ?? `${row.provider}:${row.external_id}`;
}

export function ReviewsDue() {
  const query = useReviewsDue(PAGE_SIZE);
  const { principal } = useAuth();
  const canDismiss = principal !== null && hasAnyRole(principal.roles, REVIEW_DISMISS_ROLES);
  const dismiss = useDismissReview();
  // The row awaiting a dismiss confirmation, if any (one dialog at a time).
  const [confirming, setConfirming] = useState<ReviewDueOut | null>(null);

  // The contributor cell closes over nothing external now, but the dismiss
  // cell closes over canDismiss/setConfirming, so memoize on those.
  const columns: readonly TableColumn<ReviewDueOut>[] = useMemo(() => {
    const base: TableColumn<ReviewDueOut>[] = [
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
        render: (row) => <Link to={`/contributors/${row.contributor_id}`}>{rowLabel(row)}</Link>,
      },
    ];
    if (canDismiss) {
      base.push({
        key: "dismiss",
        header: "Actions",
        render: (row) => (
          <button type="button" onClick={() => setConfirming(row)}>
            Dismiss
          </button>
        ),
      });
    }
    return base;
  }, [canDismiss]);

  return (
    <section>
      <h1>Reviews due</h1>
      <QueryBoundary query={query} capability="view reviews due">
        {(data) => (
          <>
            <Table
              columns={columns}
              rows={data.due}
              getRowKey={(row) => row.id}
              emptyState={<p>No reviews due.</p>}
            />
            <p>
              This queue is read-only for scheduling: rows move when the contributor's next quiz
              attempt is ingested. Dismissing a row removes a stale entry (e.g. a departed
              contributor); a later attempt reopens it.
            </p>
          </>
        )}
      </QueryBoundary>

      {dismiss.isError && <ErrorState error={dismiss.error} />}

      {confirming !== null && (
        <div role="dialog" aria-modal="true" aria-label="Confirm dismissing this review">
          <h2>Dismiss this review?</h2>
          <p>
            It leaves the queue for {rowLabel(confirming)} ({humanizeCategory(confirming.category)}
            ). A newer quiz attempt reopens it.
          </p>
          <button
            type="button"
            disabled={dismiss.isPending}
            onClick={() => {
              dismiss.mutate(confirming.id, { onSuccess: () => setConfirming(null) });
            }}
          >
            Confirm
          </button>
          <button type="button" onClick={() => setConfirming(null)}>
            Cancel
          </button>
        </div>
      )}
    </section>
  );
}

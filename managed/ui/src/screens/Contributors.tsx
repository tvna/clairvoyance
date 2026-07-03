import { useState } from "react";
import { Link } from "react-router-dom";
import { useContributors } from "../api/queries";
import type { ContributorOut } from "../api/schemas";
import { DateCell } from "../components/DateCell";
import { Pagination } from "../components/Pagination";
import { QueryBoundary } from "../components/QueryBoundary";
import { Table, type TableColumn } from "../components/Table";

const PAGE_SIZE = 50;

export function displayName(contributor: ContributorOut): string {
  return contributor.display_name ?? `${contributor.provider}:${contributor.external_id}`;
}

const COLUMNS: readonly TableColumn<ContributorOut>[] = [
  {
    key: "name",
    header: "Name",
    render: (contributor) => (
      <Link to={`/contributors/${contributor.id}`}>{displayName(contributor)}</Link>
    ),
  },
  { key: "provider", header: "Provider", render: (contributor) => contributor.provider },
  { key: "external_id", header: "External ID", render: (contributor) => contributor.external_id },
  { key: "email", header: "Email", render: (contributor) => contributor.email ?? "" },
  { key: "active", header: "Active", render: (contributor) => (contributor.active ? "Yes" : "No") },
  {
    key: "created_at",
    header: "Created",
    render: (contributor) => <DateCell value={contributor.created_at} />,
  },
];

export function Contributors() {
  const [offset, setOffset] = useState(0);
  const query = useContributors(PAGE_SIZE, offset);

  return (
    <section>
      <h1>Contributors</h1>
      <QueryBoundary query={query} capability="view contributors">
        {(data) => (
          <>
            <Table
              columns={COLUMNS}
              rows={data.contributors}
              getRowKey={(contributor) => contributor.id}
              emptyState={
                <p>
                  No contributors yet. Mint a collector token and point a client at this
                  organization.
                </p>
              }
            />
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

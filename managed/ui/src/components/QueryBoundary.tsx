import type { UseQueryResult } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { ForbiddenError, NotFoundError } from "../api/errors";
import { ErrorState } from "./ErrorState";
import { ForbiddenView } from "./ForbiddenView";

/**
 * Shared loading/forbidden/error branching so screens only render their
 * data state (design §8: "screens render states, they do not interpret
 * status codes individually"). `notFound` is optional — only the
 * contributor summary screen needs a 404 state distinct from the generic
 * error view.
 */
export function QueryBoundary<T>({
  query,
  capability,
  loadingLabel = "Loading…",
  notFound,
  children,
}: {
  query: UseQueryResult<T, unknown>;
  capability: string;
  loadingLabel?: string;
  notFound?: ReactNode;
  children: (data: T) => ReactNode;
}) {
  if (query.isPending) {
    return <p>{loadingLabel}</p>;
  }
  if (query.isError) {
    if (query.error instanceof ForbiddenError) {
      return <ForbiddenView capability={capability} />;
    }
    if (notFound !== undefined && query.error instanceof NotFoundError) {
      return <>{notFound}</>;
    }
    return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  }
  return <>{children(query.data)}</>;
}

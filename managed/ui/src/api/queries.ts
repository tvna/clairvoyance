/**
 * TanStack Query hooks over the admin API. Global QueryClient defaults
 * (retry, refetchOnWindowFocus) are set once in main.tsx.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { apiFetch } from "./client";
import {
  type AuditLogListOut,
  AuditLogListOutSchema,
  type ContributorListOut,
  ContributorListOutSchema,
  ContributorSummaryOutSchema,
  type PolicyOut,
  PolicyOutSchema,
  type PolicySettingsPatch,
  PolicySettingsPatchSchema,
  ReviewDueListOutSchema,
} from "./schemas";

function qs(params: Record<string, string | number>): string {
  return new URLSearchParams(
    Object.entries(params).map(([key, value]) => [key, String(value)]),
  ).toString();
}

export const queryKeys = {
  contributors: (limit: number, offset: number) => ["contributors", { limit, offset }] as const,
  contributorsRoot: ["contributors"] as const,
  contributorSummary: (id: string) => ["contributor-summary", id] as const,
  reviewsDue: (limit: number) => ["reviews-due", { limit }] as const,
  policies: ["policies"] as const,
  auditLogs: (limit: number, offset: number) => ["audit-logs", { limit, offset }] as const,
};

export function useContributors(limit: number, offset: number) {
  return useQuery({
    queryKey: queryKeys.contributors(limit, offset),
    queryFn: () =>
      apiFetch(`/v1/admin/contributors?${qs({ limit, offset })}`, ContributorListOutSchema),
  });
}

export function useContributorSummary(contributorId: string) {
  return useQuery({
    queryKey: queryKeys.contributorSummary(contributorId),
    queryFn: () =>
      apiFetch(`/v1/admin/contributors/${contributorId}/summary`, ContributorSummaryOutSchema),
  });
}

export function useReviewsDue(limit: number) {
  return useQuery({
    queryKey: queryKeys.reviewsDue(limit),
    queryFn: () => apiFetch(`/v1/admin/reviews/due?${qs({ limit })}`, ReviewDueListOutSchema),
  });
}

/**
 * Client-side join target for the reviews-due queue (design §7.3): reads
 * whatever contributor list pages happen to already be cached from visits
 * to the Contributors screen. Deliberately does NOT fetch — a per-row
 * summary/lookup call would run the full aggregate query and write an
 * audit row per row.
 */
export function useCachedContributorLookup(): ReadonlyMap<
  string,
  ContributorListOut["contributors"][number]
> {
  const queryClient = useQueryClient();
  // Snapshot once per mount: the contributor pages were cached (or not) by
  // earlier navigation, and nothing refetches them while this screen is up
  // (no active observer, refetchOnWindowFocus off) — so rebuilding the map
  // on every render would only churn allocations.
  return useMemo(() => {
    const cached = queryClient.getQueriesData<ContributorListOut>({
      queryKey: queryKeys.contributorsRoot,
    });
    const map = new Map<string, ContributorListOut["contributors"][number]>();
    for (const [, data] of cached) {
      if (data !== undefined) {
        for (const contributor of data.contributors) {
          map.set(contributor.id, contributor);
        }
      }
    }
    return map;
  }, [queryClient]);
}

export function usePolicies() {
  return useQuery({
    queryKey: queryKeys.policies,
    queryFn: () => apiFetch("/v1/admin/policies", PolicyOutSchema),
  });
}

export function useUpdatePolicies() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (patch: PolicySettingsPatch) =>
      apiFetch<PolicyOut>("/v1/admin/policies", PolicyOutSchema, {
        method: "PUT",
        // Defense-in-depth promised by PolicySettingsPatchSchema's contract:
        // an out-of-range patch fails here, before the network.
        body: { settings: PolicySettingsPatchSchema.parse(patch) },
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.policies });
    },
  });
}

export function useAuditLogs(limit: number, offset: number) {
  return useQuery({
    queryKey: queryKeys.auditLogs(limit, offset),
    queryFn: () =>
      apiFetch<AuditLogListOut>(
        `/v1/admin/audit-logs?${qs({ limit, offset })}`,
        AuditLogListOutSchema,
      ),
  });
}

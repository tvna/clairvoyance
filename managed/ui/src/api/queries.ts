/**
 * TanStack Query hooks over the admin API. Global QueryClient defaults
 * (retry, refetchOnWindowFocus) are set once in main.tsx.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import {
  type AuditLogListOut,
  AuditLogListOutSchema,
  ContributorListOutSchema,
  ContributorSummaryOutSchema,
  type PolicyOut,
  PolicyOutSchema,
  type PolicySettingsPatch,
  PolicySettingsPatchSchema,
  type ReviewDismissOut,
  ReviewDismissOutSchema,
  ReviewDueListOutSchema,
} from "./schemas";

function qs(params: Record<string, string | number>): string {
  return new URLSearchParams(
    Object.entries(params).map(([key, value]) => [key, String(value)]),
  ).toString();
}

export const queryKeys = {
  contributors: (limit: number, offset: number, q: string) =>
    ["contributors", { limit, offset, q }] as const,
  contributorSummary: (id: string) => ["contributor-summary", id] as const,
  reviewsDue: (limit: number) => ["reviews-due", { limit }] as const,
  reviewsDueRoot: ["reviews-due"] as const,
  policies: ["policies"] as const,
  auditLogs: (limit: number, offset: number) => ["audit-logs", { limit, offset }] as const,
};

export function useContributors(limit: number, offset: number, q: string) {
  return useQuery({
    queryKey: queryKeys.contributors(limit, offset, q),
    queryFn: () =>
      apiFetch(
        // `q` is a server-side partial match (design §14 gap 1); omit it when
        // empty so the unfiltered list query key and URL stay stable.
        `/v1/admin/contributors?${qs(q === "" ? { limit, offset } : { limit, offset, q })}`,
        ContributorListOutSchema,
      ),
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
 * Dismiss a review schedule (design §14 gap 5). On success the reviews-due
 * query is invalidated so the dismissed row leaves the queue; the server hides
 * dismissed rows and reopens them when a newer quiz attempt arrives.
 */
export function useDismissReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scheduleId: string) =>
      apiFetch<ReviewDismissOut>(
        `/v1/admin/reviews/${scheduleId}/dismiss`,
        ReviewDismissOutSchema,
        { method: "POST" },
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.reviewsDueRoot });
    },
  });
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

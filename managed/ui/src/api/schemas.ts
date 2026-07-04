/**
 * Zod schemas mirroring app/schemas/admin.py and app/schemas/collector.py
 * (design doc §4: "a contract drift fails a test instead of rendering
 * `undefined`"). Field-for-field mirror, including where the Python side
 * types something loosely (e.g. `dict[str, int]`, plain `str` categories)
 * rather than with its own Literal — see vocabulary.ts for why.
 */

import { z } from "zod";

const isoDateTime = z.string().refine((value) => !Number.isNaN(Date.parse(value)), {
  message: "not a valid ISO datetime string",
});

export const ContributorOutSchema = z.object({
  id: z.uuid(),
  provider: z.string(),
  external_id: z.string(),
  display_name: z.string().nullable(),
  email: z.string().nullable(),
  active: z.boolean(),
  created_at: isoDateTime,
});
export type ContributorOut = z.infer<typeof ContributorOutSchema>;

export const ContributorListOutSchema = z.object({
  contributors: z.array(ContributorOutSchema),
  total: z.number().int(),
});
export type ContributorListOut = z.infer<typeof ContributorListOutSchema>;

export const QuizStatsSchema = z.object({
  attempts: z.number().int(),
  correct: z.number().int(),
  // Buckets do NOT partition attempts (design §7.2) — sum(calibration) can
  // be < attempts. Never validate or assert sum === attempts here or in a
  // consumer.
  calibration: z.record(z.string(), z.number().int()),
});
export type QuizStats = z.infer<typeof QuizStatsSchema>;

export const ContributorSummaryOutSchema = z.object({
  contributor: ContributorOutSchema,
  events_total: z.number().int(),
  events_by_category: z.record(z.string(), z.number().int()),
  quiz: QuizStatsSchema,
  last_event_at: isoDateTime.nullable(),
});
export type ContributorSummaryOut = z.infer<typeof ContributorSummaryOutSchema>;

export const ReviewDueOutSchema = z.object({
  // The schedule's own id, so a row can address the dismiss write (§14 gap 5).
  id: z.uuid(),
  contributor_id: z.uuid(),
  // Identity carried on the row (design §14 gap 4) — the queue reads these
  // directly instead of joining names client-side from the cached list.
  display_name: z.string().nullable(),
  provider: z.string(),
  external_id: z.string(),
  category: z.string(),
  signal: z.string().nullable(),
  due_at: isoDateTime,
  interval_days: z.number().int(),
  last_outcome: z.string().nullable(),
});
export type ReviewDueOut = z.infer<typeof ReviewDueOutSchema>;

export const ReviewDueListOutSchema = z.object({
  due: z.array(ReviewDueOutSchema),
});
export type ReviewDueListOut = z.infer<typeof ReviewDueListOutSchema>;

export const ReviewDismissOutSchema = z.object({
  id: z.uuid(),
  status: z.string(),
  dismissed_at: isoDateTime.nullable(),
  dismissed_by: z.string().nullable(),
});
export type ReviewDismissOut = z.infer<typeof ReviewDismissOutSchema>;

export const PolicySettingsSchema = z.object({
  collect_enabled: z.boolean(),
  allow_context_summary: z.boolean(),
  retention_days: z.number().int().min(1).max(3650),
});
export type PolicySettings = z.infer<typeof PolicySettingsSchema>;

export const PolicyOutSchema = z.object({
  organization_key: z.string(),
  settings: PolicySettingsSchema,
});
export type PolicyOut = z.infer<typeof PolicyOutSchema>;

// Outgoing request body (PolicySettingsPatch mirror). Validated before send
// (useUpdatePolicies) as defense-in-depth, not because the server trusts
// the client.
export const PolicySettingsPatchSchema = z
  .object({
    collect_enabled: z.boolean().optional(),
    allow_context_summary: z.boolean().optional(),
    retention_days: z.number().int().min(1).max(3650).optional(),
  })
  .strict();
export type PolicySettingsPatch = z.infer<typeof PolicySettingsPatchSchema>;

export const AuditLogOutSchema = z.object({
  actor: z.string(),
  action: z.string(),
  target_type: z.string().nullable(),
  target_id: z.string().nullable(),
  created_at: isoDateTime,
});
export type AuditLogOut = z.infer<typeof AuditLogOutSchema>;

export const AuditLogListOutSchema = z.object({
  logs: z.array(AuditLogOutSchema),
  total: z.number().int(),
});
export type AuditLogListOut = z.infer<typeof AuditLogListOutSchema>;

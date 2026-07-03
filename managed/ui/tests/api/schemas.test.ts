import { describe, expect, it } from "vitest";
import {
  AuditLogListOutSchema,
  ContributorListOutSchema,
  ContributorSummaryOutSchema,
  PolicyOutSchema,
  PolicySettingsPatchSchema,
  ReviewDueListOutSchema,
} from "../../src/api/schemas";
import auditLogs from "./fixtures/audit_logs.json";
import contributorList from "./fixtures/contributor_list.json";
import contributorSummary from "./fixtures/contributor_summary.json";
import policy from "./fixtures/policy.json";
import reviewsDue from "./fixtures/reviews_due.json";

describe("admin API contract schemas", () => {
  it("parses GET /v1/admin/contributors", () => {
    const parsed = ContributorListOutSchema.parse(contributorList);
    expect(parsed.total).toBe(2);
    expect(parsed.contributors[1]?.display_name).toBeNull();
  });

  it("parses GET /v1/admin/contributors/{id}/summary", () => {
    const parsed = ContributorSummaryOutSchema.parse(contributorSummary);
    expect(parsed.quiz.attempts).toBe(6);
    // Buckets do NOT partition attempts (design §7.2) — must not assert
    // sum(calibration) === attempts anywhere, including here.
    const calibrationSum = Object.values(parsed.quiz.calibration).reduce((a, b) => a + b, 0);
    expect(calibrationSum).toBeLessThan(parsed.quiz.attempts);
  });

  it("parses GET /v1/admin/reviews/due, preserving null signal", () => {
    const parsed = ReviewDueListOutSchema.parse(reviewsDue);
    expect(parsed.due).toHaveLength(2);
    expect(parsed.due[1]?.signal).toBeNull();
  });

  it("parses GET /v1/admin/policies", () => {
    const parsed = PolicyOutSchema.parse(policy);
    expect(parsed.organization_key).toBe("acme");
    expect(parsed.settings.allow_context_summary).toBe(false);
  });

  it("parses GET /v1/admin/audit-logs", () => {
    const parsed = AuditLogListOutSchema.parse(auditLogs);
    expect(parsed.logs).toHaveLength(2);
    expect(parsed.logs[0]?.target_type).toBeNull();
  });

  it("rejects a policy patch with a null field (mirrors reject_null_updates)", () => {
    // The Python PolicySettingsPatch rejects explicit nulls; the outgoing
    // request schema is strict about unknown keys but zod's .optional()
    // still allows `undefined`. Explicit null must fail client-side too,
    // so a bad UI state is caught before the request leaves the browser.
    const result = PolicySettingsPatchSchema.safeParse({ collect_enabled: null });
    expect(result.success).toBe(false);
  });

  it("rejects an unknown field on the policy patch", () => {
    const result = PolicySettingsPatchSchema.safeParse({ not_a_real_field: true });
    expect(result.success).toBe(false);
  });
});

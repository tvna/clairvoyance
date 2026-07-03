import { expect, type Page, test } from "@playwright/test";

const ROLES = ["org_admin", "team_manager", "coach", "auditor"] as const;

async function signInAs(
  page: Page,
  opts: { sub: string; org: string; roles: readonly string[]; startPath?: string },
) {
  await page.goto(opts.startPath ?? "/ui/");
  await page.getByRole("button", { name: "Sign in" }).click();
  // Full-page redirect to the stub issuer (design §13's real, non-mocked flow).
  await page.waitForURL(/\/issuer\/authorize/);

  await page.getByLabel("Organization key").fill(opts.org);
  await page.getByLabel("Subject").fill(opts.sub);
  for (const role of ROLES) {
    const checkbox = page.locator(`input[name="roles"][value="${role}"]`);
    const shouldBeChecked = opts.roles.includes(role);
    if ((await checkbox.isChecked()) !== shouldBeChecked) {
      await checkbox.setChecked(shouldBeChecked);
    }
  }
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(
    (url) => url.pathname.startsWith("/ui/") && !url.pathname.includes("/issuer/"),
  );
}

test.describe("admin UI smoke (design §13)", () => {
  test("org_admin signs in, loads all five screens, and edits a policy", async ({ page }) => {
    await signInAs(page, { sub: "org-admin-e2e@example.com", org: "acme", roles: ["org_admin"] });

    await expect(page.getByRole("heading", { name: "Contributors" })).toBeVisible();

    await page.getByRole("link", { name: "Reviews due" }).click();
    await expect(page.getByRole("heading", { name: "Reviews due" })).toBeVisible();

    await page.getByRole("link", { name: "Policies" }).click();
    await expect(page.getByRole("heading", { name: "Policies" })).toBeVisible();

    const retentionInput = page.getByLabel("Retention days");
    await expect(retentionInput).toBeEnabled();
    await retentionInput.fill("400");
    await page.getByRole("button", { name: "Save" }).click();
    // No error state after the write (design §7.4's partial-patch PUT).
    await expect(page.getByRole("alert")).toHaveCount(0);

    await page.getByRole("link", { name: "Audit logs" }).click();
    await expect(page.getByRole("heading", { name: "Audit logs" })).toBeVisible();
    // Viewing audit logs is itself audited (design §7.5).
    await expect(
      page.getByText("Viewing this screen writes an audit row of its own."),
    ).toBeVisible();

    // Contributors screen renders its designed empty state cleanly on a
    // fresh database rather than erroring (design §7.1).
    await page.getByRole("link", { name: "Contributors" }).click();
    await expect(page.getByRole("heading", { name: "Contributors" })).toBeVisible();
    await expect(page.getByRole("alert")).toHaveCount(0);
  });

  test("coach sees the 403 view on a direct audit-logs request", async ({ page }) => {
    await signInAs(page, { sub: "coach-e2e@example.com", org: "acme", roles: ["coach"] });
    await expect(page.getByRole("heading", { name: "Contributors" })).toBeVisible();

    // Nav hides Audit logs for coach as a courtesy only (design §2).
    await expect(page.getByRole("link", { name: "Audit logs" })).toHaveCount(0);

    // A direct request to a role-denied route still hits the server and
    // gets a real 403. Tokens are in-memory only (design §5) and do not
    // survive a hard navigation, so re-signing in starting at /ui/audit
    // exercises the redirect-back-to-the-original-route path (RequireAuth
    // -> SignIn -> stub issuer -> Callback) rather than a page.goto that
    // would just drop the session and land back on the sign-in screen.
    await signInAs(page, {
      sub: "coach-e2e@example.com",
      org: "acme",
      roles: ["coach"],
      startPath: "/ui/audit",
    });
    await expect(page.getByRole("heading", { name: "Access denied" })).toBeVisible();

    // Policies stays view-only for a non-org_admin (design §7.4).
    await page.getByRole("link", { name: "Policies" }).click();
    await expect(page.getByRole("heading", { name: "Policies" })).toBeVisible();
    await expect(page.getByLabel("Retention days")).toBeDisabled();
    await expect(page.getByRole("button", { name: "Save" })).toHaveCount(0);
  });
});

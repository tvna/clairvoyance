import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Policies } from "../../src/screens/Policies";
import policyFixture from "../api/fixtures/policy.json";
import { jsonResponse, makeAuthState, renderWithProviders } from "../testUtils";

describe("Policies screen", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders read-only for a non-org_admin role (design §7.4)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, policyFixture)));

    renderWithProviders(<Policies />, {
      authState: makeAuthState({
        principal: {
          subject: "coach@example.com",
          organizationKey: "acme",
          roles: new Set(["coach"]),
        },
      }),
    });

    const collectCheckbox = await screen.findByRole("checkbox", { name: /Collect enabled/ });
    expect(collectCheckbox).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Save" })).not.toBeInTheDocument();
  });

  it("requires typing ENABLE before turning allow_context_summary on", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, policyFixture)));

    renderWithProviders(<Policies />);

    const toggle = await screen.findByRole("checkbox", { name: /Allow context summary/ });
    expect(toggle).not.toBeChecked();
    await user.click(toggle);

    // Turning on is not immediate — a typed-confirm dialog gates it.
    expect(toggle).not.toBeChecked();
    const dialog = screen.getByRole("dialog");
    const confirmButton = within(dialog).getByRole("button", { name: "Confirm" });
    expect(confirmButton).toBeDisabled();

    await user.type(within(dialog).getByLabelText(/Type ENABLE to confirm/), "not-quite");
    expect(confirmButton).toBeDisabled();

    await user.clear(within(dialog).getByLabelText(/Type ENABLE to confirm/));
    await user.type(within(dialog).getByLabelText(/Type ENABLE to confirm/), "ENABLE");
    expect(confirmButton).toBeEnabled();
    await user.click(confirmButton);

    expect(toggle).toBeChecked();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("turning allow_context_summary off does not require confirmation", async () => {
    const user = userEvent.setup();
    const enabledFixture = {
      ...policyFixture,
      settings: { ...policyFixture.settings, allow_context_summary: true },
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, enabledFixture)));

    renderWithProviders(<Policies />);

    const toggle = await screen.findByRole("checkbox", { name: /Allow context summary/ });
    expect(toggle).toBeChecked();
    await user.click(toggle);

    expect(toggle).not.toBeChecked();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows the deferred-enforcement warning when tightening retention and submits a partial patch", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === "PUT") {
        return Promise.resolve(
          jsonResponse(200, {
            ...policyFixture,
            settings: { ...policyFixture.settings, retention_days: 30 },
          }),
        );
      }
      return Promise.resolve(jsonResponse(200, policyFixture));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<Policies />);

    const retentionInput = await screen.findByLabelText("Retention days");
    await user.clear(retentionInput);
    await user.type(retentionInput, "30");

    expect(
      screen.getByText(/enforced by the daily beat task, not immediately/),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      const putCall = fetchMock.mock.calls.find(
        ([, init]) => (init as RequestInit | undefined)?.method === "PUT",
      );
      expect(putCall).toBeDefined();
      const body = JSON.parse((putCall?.[1] as RequestInit).body as string);
      // Partial patch: only the changed field is sent (PolicySettingsPatch shape).
      expect(body).toEqual({ settings: { retention_days: 30 } });
    });
  });
});

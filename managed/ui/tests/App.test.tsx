import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/App";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("App boot", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/ui/");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a configuration error when /ui/config.json is invalid", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { issuer: "https://idp.example.com" })),
    );
    render(<App />);
    expect(await screen.findByText("Configuration error")).toBeInTheDocument();
  });

  it("boots the router and redirects an unauthenticated visitor to sign-in", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(200, {
          issuer: "https://idp.example.com",
          client_id: "clairvoyance-ui",
          audience: "clairvoyance-managed",
          org_claim: "org",
          roles_claim: "roles",
        }),
      ),
    );
    render(<App />);
    expect(await screen.findByRole("button", { name: "Sign in" })).toBeInTheDocument();
  });
});

/**
 * Runtime configuration (design §6): the ui image's entrypoint renders
 * /ui/config.json from environment at container start. No secrets — every
 * value here is public by definition (authorize-redirect params or claim
 * *names*, not values).
 */

import { z } from "zod";

export const RuntimeConfigSchema = z.object({
  issuer: z.string().min(1),
  client_id: z.string().min(1),
  audience: z.string().min(1),
  org_claim: z.string().min(1),
  roles_claim: z.string().min(1),
  authorization_endpoint: z.string().min(1).optional(),
  token_endpoint: z.string().min(1).optional(),
  end_session_endpoint: z.string().min(1).optional(),
});
export type RuntimeConfig = z.infer<typeof RuntimeConfigSchema>;

export class RuntimeConfigError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "RuntimeConfigError";
  }
}

export async function loadRuntimeConfig(configUrl = "/ui/config.json"): Promise<RuntimeConfig> {
  let response: Response;
  try {
    response = await fetch(configUrl, { cache: "no-store" });
  } catch (cause) {
    throw new RuntimeConfigError(`failed to fetch ${configUrl}`, { cause });
  }
  if (!response.ok) {
    throw new RuntimeConfigError(`${configUrl} returned HTTP ${response.status}`);
  }
  const json: unknown = await response.json();
  const parsed = RuntimeConfigSchema.safeParse(json);
  if (!parsed.success) {
    throw new RuntimeConfigError(
      `${configUrl} did not match the expected shape: ${parsed.error.message}`,
    );
  }
  return parsed.data;
}

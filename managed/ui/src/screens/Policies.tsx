import { useEffect, useState } from "react";
import { usePolicies, useUpdatePolicies } from "../api/queries";
import type { PolicySettings, PolicySettingsPatch } from "../api/schemas";
import { useAuth } from "../auth/AuthContext";
import { hasAnyRole, POLICY_WRITE_ROLES } from "../auth/roles";
import { ErrorState } from "../components/ErrorState";
import { QueryBoundary } from "../components/QueryBoundary";

const CONFIRM_PHRASE = "ENABLE";

function PolicyForm({ settings, canEdit }: { settings: PolicySettings; canEdit: boolean }) {
  const mutation = useUpdatePolicies();

  const [collectEnabled, setCollectEnabled] = useState(settings.collect_enabled);
  const [allowContextSummary, setAllowContextSummary] = useState(settings.allow_context_summary);
  const [retentionDays, setRetentionDays] = useState(settings.retention_days);
  const [confirmingEnable, setConfirmingEnable] = useState(false);
  const [confirmText, setConfirmText] = useState("");

  // Re-seed local form state whenever the server settings change (e.g.
  // after a successful save invalidates and refetches the policy query).
  useEffect(() => {
    setCollectEnabled(settings.collect_enabled);
    setAllowContextSummary(settings.allow_context_summary);
    setRetentionDays(settings.retention_days);
  }, [settings]);

  function handleToggleAllowContextSummary(next: boolean) {
    if (next) {
      // Turning ON requires a typed confirmation (design §7.4); turning
      // off stays one click — asymmetric friction matching the
      // default-deny stance.
      setConfirmingEnable(true);
      return;
    }
    setAllowContextSummary(false);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const patch: PolicySettingsPatch = {};
    if (collectEnabled !== settings.collect_enabled) {
      patch.collect_enabled = collectEnabled;
    }
    if (allowContextSummary !== settings.allow_context_summary) {
      patch.allow_context_summary = allowContextSummary;
    }
    if (retentionDays !== settings.retention_days) {
      patch.retention_days = retentionDays;
    }
    mutation.mutate(patch);
  }

  return (
    <>
      <form onSubmit={handleSubmit}>
        <fieldset disabled={!canEdit}>
          {!canEdit && <legend>Read-only — org_admin can change these settings.</legend>}

          <div>
            <label>
              <input
                type="checkbox"
                checked={collectEnabled}
                onChange={(event) => setCollectEnabled(event.target.checked)}
              />
              Collect enabled
            </label>
            <p>Off means clients get "do not collect" from GET /v1/client/policy.</p>
          </div>

          <div>
            <label>
              <input
                type="checkbox"
                checked={allowContextSummary}
                onChange={(event) => handleToggleAllowContextSummary(event.target.checked)}
              />
              Allow context summary
            </label>
            <p>
              Enabling stores abstracted work content from contributors' sessions. The server
              confirms storage per event (<code>context_summary_stored</code>).
            </p>
          </div>

          <div>
            <label htmlFor="retention-days">Retention days</label>
            <input
              id="retention-days"
              type="number"
              min={1}
              max={3650}
              value={retentionDays}
              onChange={(event) => setRetentionDays(Number(event.target.value))}
            />
            <p>
              Deletion is permanent, cascades to quiz attempts, and cuts on <code>occurred_at</code>
              . Set <code>CLAIRVOYANCE_RETENTION_DRY_RUN=true</code> to verify before tightening.
            </p>
            {retentionDays < settings.retention_days && (
              <p role="status">
                A tightened retention period is enforced by the daily beat task, not immediately.
              </p>
            )}
          </div>

          {canEdit && (
            <button type="submit" disabled={mutation.isPending}>
              Save
            </button>
          )}
        </fieldset>
      </form>
      {mutation.isError && <ErrorState error={mutation.error} />}

      {confirmingEnable && (
        <div role="dialog" aria-modal="true" aria-label="Confirm enabling context summary storage">
          <h2>Enable context summary storage?</h2>
          <p>This stores abstracted work content from contributors' sessions.</p>
          <label htmlFor="confirm-enable-text">
            Type {CONFIRM_PHRASE} to confirm
            <input
              id="confirm-enable-text"
              value={confirmText}
              onChange={(event) => setConfirmText(event.target.value)}
            />
          </label>
          <button
            type="button"
            disabled={confirmText !== CONFIRM_PHRASE}
            onClick={() => {
              setAllowContextSummary(true);
              setConfirmingEnable(false);
              setConfirmText("");
            }}
          >
            Confirm
          </button>
          <button
            type="button"
            onClick={() => {
              setConfirmingEnable(false);
              setConfirmText("");
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </>
  );
}

export function Policies() {
  const { principal } = useAuth();
  const query = usePolicies();
  const canEdit = principal !== null && hasAnyRole(principal.roles, POLICY_WRITE_ROLES);

  return (
    <section>
      <h1>Policies</h1>
      <QueryBoundary query={query} capability="view organization policies">
        {(data) => <PolicyForm settings={data.settings} canEdit={canEdit} />}
      </QueryBoundary>
    </section>
  );
}

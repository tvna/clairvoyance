import { describeApiError } from "../api/describeError";
import styles from "./ErrorState.module.css";

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { message } = describeApiError(error);
  return (
    <div className={styles.state} role="alert">
      <p>{message}</p>
      {onRetry !== undefined && (
        <button type="button" className={styles.retry} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

import { CALIBRATION_ORDER } from "../api/vocabulary";
import styles from "./CalibrationBar.module.css";

const CHART_WIDTH = 320;
const BAR_HEIGHT = 20;

const SEGMENT_COLOR: Record<(typeof CALIBRATION_ORDER)[number], string> = {
  accurate: "var(--color-positive)",
  overconfident: "var(--color-warning)",
  underconfident: "var(--color-warning)",
  unknown: "var(--color-neutral)",
};

/**
 * Segmented bar for the quiz calibration distribution (design §7.2). The
 * buckets do NOT partition attempts — calibration is optional on quiz
 * events, and the aggregate drops unreported values rather than folding
 * them into "unknown" — so segments are sized against their own sum, and
 * "N unreported" (attempts - sum) is shown beside it. Never assert
 * sum(segments) === attempts.
 */
export function CalibrationBar({
  attempts,
  calibration,
}: {
  attempts: number;
  calibration: Record<string, number>;
}) {
  const segments = CALIBRATION_ORDER.map((key) => ({ key, count: calibration[key] ?? 0 })).filter(
    (segment) => segment.count > 0,
  );
  const sum = segments.reduce((total, segment) => total + segment.count, 0);
  const unreported = Math.max(0, attempts - sum);

  if (sum === 0) {
    return <p className={styles.unreported}>{unreported} unreported</p>;
  }

  let x = 0;
  const bars = segments.map((segment) => {
    const width = (segment.count / sum) * CHART_WIDTH;
    const bar = (
      <rect
        key={segment.key}
        x={x}
        y={0}
        width={width}
        height={BAR_HEIGHT}
        fill={SEGMENT_COLOR[segment.key]}
      />
    );
    x += width;
    return bar;
  });

  return (
    <div>
      <svg
        role="img"
        aria-label="Calibration distribution"
        viewBox={`0 0 ${CHART_WIDTH} ${BAR_HEIGHT}`}
        width="100%"
        height={BAR_HEIGHT}
      >
        {bars}
      </svg>
      <ul className={styles.legend}>
        {segments.map((segment) => (
          <li key={segment.key}>
            <span
              className={styles.swatch}
              style={{ backgroundColor: SEGMENT_COLOR[segment.key] }}
            />
            {segment.key}: {segment.count}
          </li>
        ))}
      </ul>
      {unreported > 0 && <p className={styles.unreported}>{unreported} unreported</p>}
    </div>
  );
}

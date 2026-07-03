import { CATEGORY_ORDER, categoryColorVar, humanizeCategory } from "../api/vocabulary";
import styles from "./BarChart.module.css";

const ROW_HEIGHT = 28;
const CHART_WIDTH = 320;
const LABEL_WIDTH = 140;
const BAR_AREA_WIDTH = CHART_WIDTH - LABEL_WIDTH - 32;

/** Horizontal bar list, one measure (count) per category (design §10). */
export function BarChart({ data, ariaLabel }: { data: Record<string, number>; ariaLabel: string }) {
  const entries = Object.entries(data)
    .filter(([, count]) => count > 0)
    .sort(([categoryA, countA], [categoryB, countB]) => {
      if (countB !== countA) {
        return countB - countA;
      }
      return (
        CATEGORY_ORDER.indexOf(categoryA as (typeof CATEGORY_ORDER)[number]) -
        CATEGORY_ORDER.indexOf(categoryB as (typeof CATEGORY_ORDER)[number])
      );
    });

  if (entries.length === 0) {
    return <p className={styles.empty}>No events recorded.</p>;
  }

  const maxCount = Math.max(...entries.map(([, count]) => count));
  const height = entries.length * ROW_HEIGHT;

  return (
    <svg
      role="img"
      aria-label={ariaLabel}
      viewBox={`0 0 ${CHART_WIDTH} ${height}`}
      width="100%"
      height={height}
    >
      {entries.map(([category, count], index) => {
        const y = index * ROW_HEIGHT;
        const barWidth = maxCount === 0 ? 0 : (count / maxCount) * BAR_AREA_WIDTH;
        return (
          <g key={category} transform={`translate(0, ${y})`}>
            <text
              x={0}
              y={ROW_HEIGHT / 2}
              dominantBaseline="middle"
              fontSize={12}
              className={styles.label}
            >
              {humanizeCategory(category)}
            </text>
            <rect
              x={LABEL_WIDTH}
              y={4}
              width={barWidth}
              height={ROW_HEIGHT - 12}
              fill={categoryColorVar(category)}
              rx={2}
            />
            <text
              x={LABEL_WIDTH + barWidth + 6}
              y={ROW_HEIGHT / 2}
              dominantBaseline="middle"
              fontSize={12}
              className={styles.label}
            >
              {count}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

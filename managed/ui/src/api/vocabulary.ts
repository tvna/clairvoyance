/**
 * Vocabulary shared with app/schemas/collector.py (Category/Outcome/
 * Confidence/Calibration) and store.md. This module is the single source
 * for the fixed ordinal ordering the design doc requires (§7.2, §10): the
 * same category or calibration bucket renders with the same color/position
 * on every screen. The admin API's *read* models (admin.py) type these
 * fields loosely as `str`/`dict[str, int]` — only the collector's *write*
 * contract enforces the Literal — so schemas.ts intentionally does not
 * constrain response parsing to this vocabulary; this module is presentation
 * ordering only.
 */

export const CATEGORY_ORDER = [
  "avoidance",
  "mislabeled-technical",
  "loss-aversion",
  "values-conflict",
  "no-experiment",
  "authority-dependence",
  "other",
] as const;

export type Category = (typeof CATEGORY_ORDER)[number];

export const CALIBRATION_ORDER = [
  "accurate",
  "overconfident",
  "underconfident",
  "unknown",
] as const;

export type Calibration = (typeof CALIBRATION_ORDER)[number];

export function categoryColorVar(category: string): string {
  const index = CATEGORY_ORDER.indexOf(category as Category);
  return `var(--category-${index === -1 ? 6 : index})`;
}

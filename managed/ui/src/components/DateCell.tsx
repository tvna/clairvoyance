/**
 * Renders in the viewer's local timezone with the UTC value on hover
 * (design §7: "the API is timezone-aware end to end, the UI must not
 * truncate that").
 */
export function DateCell({ value }: { value: string }) {
  const date = new Date(value);
  return (
    <time dateTime={value} title={`UTC: ${date.toISOString()}`}>
      {date.toLocaleString()}
    </time>
  );
}

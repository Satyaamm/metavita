/** Pure chart math — scale values to pixel heights for the SVG bar chart. */

export function scaleBars(values: number[], maxHeight: number): number[] {
  const max = Math.max(1, ...values);
  return values.map((v) => Math.round((v / max) * maxHeight));
}

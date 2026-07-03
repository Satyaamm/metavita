import { describe, expect, it } from "vitest";
import { scaleBars } from "./chart";

describe("scaleBars", () => {
  it("scales values to the max height", () => {
    expect(scaleBars([0, 5, 10], 100)).toEqual([0, 50, 100]);
  });

  it("handles all-zero without dividing by zero", () => {
    expect(scaleBars([0, 0, 0], 80)).toEqual([0, 0, 0]);
  });

  it("rounds to whole pixels", () => {
    expect(scaleBars([1, 3], 100)).toEqual([33, 100]);
  });
});

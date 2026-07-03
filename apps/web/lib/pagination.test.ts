import { describe, expect, it } from "vitest";
import { clampPage, itemRange, offsetFor, pageCount, pageWindow } from "./pagination";

describe("pagination helpers", () => {
  it("pageCount rounds up and is at least 1", () => {
    expect(pageCount(0, 20)).toBe(1);
    expect(pageCount(20, 20)).toBe(1);
    expect(pageCount(21, 20)).toBe(2);
    expect(pageCount(95, 20)).toBe(5);
  });

  it("clampPage keeps page within [1, pageCount]", () => {
    expect(clampPage(0, 100, 20)).toBe(1);
    expect(clampPage(99, 100, 20)).toBe(5);
    expect(clampPage(3, 100, 20)).toBe(3);
  });

  it("offsetFor computes the zero-based offset", () => {
    expect(offsetFor(1, 20)).toBe(0);
    expect(offsetFor(3, 20)).toBe(40);
  });

  it("itemRange gives the 1-based visible range", () => {
    expect(itemRange(1, 20, 95)).toEqual({ from: 1, to: 20 });
    expect(itemRange(5, 20, 95)).toEqual({ from: 81, to: 95 });
    expect(itemRange(1, 20, 0)).toEqual({ from: 0, to: 0 });
  });

  it("pageWindow returns clamped page numbers around current", () => {
    expect(pageWindow(1, 10, 2)).toEqual([1, 2, 3]);
    expect(pageWindow(5, 10, 2)).toEqual([3, 4, 5, 6, 7]);
    expect(pageWindow(10, 10, 2)).toEqual([8, 9, 10]);
  });
});

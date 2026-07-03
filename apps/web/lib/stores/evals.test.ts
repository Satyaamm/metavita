import { describe, expect, it } from "vitest";
import { parseQuestions } from "./evals";

describe("parseQuestions", () => {
  it("parses one question per non-empty line", () => {
    expect(parseQuestions("What is X?\n\nWhat is Y?  ")).toEqual([
      { question: "What is X?", expected: null },
      { question: "What is Y?", expected: null },
    ]);
  });

  it("splits 'question | expected'", () => {
    expect(parseQuestions("What color is the sky? | blue")).toEqual([
      { question: "What color is the sky?", expected: "blue" },
    ]);
  });
});

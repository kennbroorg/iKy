import { describe, expect, it } from "vitest";

import { computeBubbleLayout } from "@/components/viz/bubble-chart";

describe("computeBubbleLayout", () => {
  it("returns positioned circles with x, y, and r", () => {
    const input = [
      { name: "A", value: 100 },
      { name: "B", value: 50 },
    ];
    const result = computeBubbleLayout(input, 400, 300);

    expect(result).toHaveLength(2);
    for (const bubble of result) {
      expect(bubble).toHaveProperty("x");
      expect(bubble).toHaveProperty("y");
      expect(bubble).toHaveProperty("r");
      expect(bubble.x).toBeGreaterThan(0);
      expect(bubble.y).toBeGreaterThan(0);
      expect(bubble.r).toBeGreaterThan(0);
    }
  });

  it("gives bigger values bigger radii", () => {
    const input = [
      { name: "Big", value: 1000 },
      { name: "Small", value: 10 },
    ];
    const result = computeBubbleLayout(input, 400, 300);

    const big = result.find((b) => b.name === "Big")!;
    const small = result.find((b) => b.name === "Small")!;

    expect(big.r).toBeGreaterThan(small.r);
  });

  it("returns [] for empty input", () => {
    expect(computeBubbleLayout([], 400, 300)).toEqual([]);
  });

  it("returns [] for null/undefined-like input", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    expect(computeBubbleLayout(null as any, 400, 300)).toEqual([]);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    expect(computeBubbleLayout(undefined as any, 400, 300)).toEqual([]);
  });

  it("preserves name and value in output", () => {
    const input = [{ name: "Test", value: 42 }];
    const result = computeBubbleLayout(input, 200, 200);

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("Test");
    expect(result[0].value).toBe(42);
  });

  it("handles single item", () => {
    const result = computeBubbleLayout(
      [{ name: "Solo", value: 100 }],
      400,
      300,
    );
    expect(result).toHaveLength(1);
    expect(result[0].r).toBeGreaterThan(0);
  });
});

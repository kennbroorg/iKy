import { describe, expect, it } from "vitest";

import { normalizeTreemapData } from "@/components/viz/treemap-chart";

describe("normalizeTreemapData", () => {
  it("converts items with 'total' key to {name, size}[]", () => {
    const input = [
      { name: "JavaScript", total: 500 },
      { name: "Python", total: 300 },
    ];
    const result = normalizeTreemapData(input);
    expect(result).toEqual([
      { name: "JavaScript", size: 500 },
      { name: "Python", size: 300 },
    ]);
  });

  it("falls back to 'value' when 'total' is missing", () => {
    const input = [
      { name: "React", value: 120 },
      { name: "Vue", value: 80 },
    ];
    const result = normalizeTreemapData(input);
    expect(result).toEqual([
      { name: "React", size: 120 },
      { name: "Vue", size: 80 },
    ]);
  });

  it("falls back to 'size' when both 'total' and 'value' are missing", () => {
    const input = [{ name: "CSS", size: 42 }];
    const result = normalizeTreemapData(input);
    expect(result).toEqual([{ name: "CSS", size: 42 }]);
  });

  it("prefers 'total' over 'value' over 'size'", () => {
    const input = [{ name: "All", total: 100, value: 50, size: 25 }];
    const result = normalizeTreemapData(input);
    expect(result).toEqual([{ name: "All", size: 100 }]);
  });

  it("returns [] for empty input", () => {
    expect(normalizeTreemapData([])).toEqual([]);
  });

  it("returns [] for null/undefined-like input", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    expect(normalizeTreemapData(null as any)).toEqual([]);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    expect(normalizeTreemapData(undefined as any)).toEqual([]);
  });

  it("defaults to 0 when no numeric field is present", () => {
    const input = [{ name: "Empty" }];
    const result = normalizeTreemapData(input);
    expect(result).toEqual([{ name: "Empty", size: 0 }]);
  });
});

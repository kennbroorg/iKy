import { describe, expect, it } from "vitest";

import { parseModuleResult } from "../result-parser";

describe("parseModuleResult", () => {
  it("parses backend result array into typed object", () => {
    const raw = [
      { module: "github" },
      { param: "johndoe" },
      { validation: "no" },
      { raw: { data: "test" } },
      { graphic: [{ details: [1, 2] }] },
      { profile: [{ name: "John" }] },
      { timeline: [{ date: "2024-01-01", action: "Created repo" }] },
      { tasks: [{ module: "twitter", param: "johndoe" }] },
    ];
    const result = parseModuleResult(raw);
    expect(result.module).toBe("github");
    expect(result.param).toBe("johndoe");
    expect(result.validation).toBe("no");
    expect(result.timeline).toHaveLength(1);
    expect(result.tasks[0].module).toBe("twitter");
  });

  it("handles missing fields gracefully", () => {
    const result = parseModuleResult([{ module: "test" }]);
    expect(result.module).toBe("test");
    expect(result.graphic).toEqual([]);
    expect(result.timeline).toEqual([]);
  });
});

import { describe, expect, it } from "vitest";

import { aggregateTimeline } from "../timeline-aggregator";
import type { TaskEntry } from "@/stores/gather-store";

describe("aggregateTimeline", () => {
  it("aggregates and sorts events newest-first", () => {
    const tasks: Record<string, TaskEntry> = {
      github: {
        taskId: "1",
        status: "success",
        result: {
          module: "github",
          param: "john",
          validation: "no",
          raw: {},
          graphic: [],
          profile: [],
          tasks: [],
          timeline: [
            { date: "2024/01/15 10:30:00", action: "Created repo" },
            { date: "2023/06/01 00:00:00", action: "Joined GitHub" },
          ],
        },
      },
      twitter: {
        taskId: "2",
        status: "success",
        result: {
          module: "twitter",
          param: "john",
          validation: "no",
          raw: {},
          graphic: [],
          profile: [],
          tasks: [],
          timeline: [
            { date: "2024/03/20 15:00:00", action: "Posted tweet" },
          ],
        },
      },
    };
    const events = aggregateTimeline(tasks);
    expect(events).toHaveLength(3);
    expect(events[0].action).toBe("Posted tweet");
    expect(events[0].source).toBe("twitter");
    expect(events[2].action).toBe("Joined GitHub");
  });

  it("returns empty array when no tasks have timeline data", () => {
    const tasks: Record<string, TaskEntry> = {
      github: {
        taskId: "1",
        status: "success",
        result: {
          module: "github",
          param: "john",
          validation: "no",
          raw: {},
          graphic: [],
          profile: [],
          tasks: [],
          timeline: [],
        },
      },
    };
    const events = aggregateTimeline(tasks);
    expect(events).toHaveLength(0);
  });

  it("skips non-success tasks", () => {
    const tasks: Record<string, TaskEntry> = {
      github: {
        taskId: "1",
        status: "error",
        error: "failed",
        result: {
          module: "github",
          param: "john",
          validation: "no",
          raw: {},
          graphic: [],
          profile: [],
          tasks: [],
          timeline: [
            { date: "2024/01/01 00:00:00", action: "Should not appear" },
          ],
        },
      },
    };
    const events = aggregateTimeline(tasks);
    expect(events).toHaveLength(0);
  });
});

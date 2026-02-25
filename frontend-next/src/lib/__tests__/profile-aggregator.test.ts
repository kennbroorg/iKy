import { describe, expect, it } from "vitest";

import { aggregateProfile } from "../profile-aggregator";
import type { TaskEntry } from "@/stores/gather-store";

describe("aggregateProfile", () => {
  it("merges profile data from multiple modules", () => {
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
          tasks: [],
          profile: [{ name: "John Doe", organization: "ACME" }],
          timeline: [],
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
          tasks: [],
          profile: [
            {
              name: "John D.",
              location: "NYC",
              photos: [{ src: "http://img.jpg" }],
            },
          ],
          timeline: [],
        },
      },
    };
    const profile = aggregateProfile(tasks);
    expect(profile.names).toContain("John Doe");
    expect(profile.names).toContain("John D.");
    expect(profile.locations).toContain("NYC");
    expect(profile.photos).toHaveLength(1);
    expect(profile.organizations).toContain("ACME");
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
          tasks: [],
          profile: [{ name: "Should Not Appear" }],
          timeline: [],
        },
      },
    };
    const profile = aggregateProfile(tasks);
    expect(profile.names).toHaveLength(0);
  });

  it("deduplicates names and emails", () => {
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
          tasks: [],
          profile: [{ name: "John", email: "john@test.com" }],
          timeline: [],
        },
      },
      gitlab: {
        taskId: "2",
        status: "success",
        result: {
          module: "gitlab",
          param: "john",
          validation: "no",
          raw: {},
          graphic: [],
          tasks: [],
          profile: [{ name: "John", email: "john@test.com" }],
          timeline: [],
        },
      },
    };
    const profile = aggregateProfile(tasks);
    expect(profile.names).toHaveLength(1);
    expect(profile.emails).toHaveLength(1);
  });

  it("aggregates geo data with module label", () => {
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
          tasks: [],
          profile: [{ geo: { lat: 40.7, lng: -74.0 } }],
          timeline: [],
        },
      },
    };
    const profile = aggregateProfile(tasks);
    expect(profile.geo).toHaveLength(1);
    expect(profile.geo[0]).toEqual({
      lat: 40.7,
      lng: -74.0,
      label: "github",
    });
  });

  it("returns empty profile when no tasks", () => {
    const profile = aggregateProfile({});
    expect(profile.names).toHaveLength(0);
    expect(profile.photos).toHaveLength(0);
    expect(profile.geo).toHaveLength(0);
  });
});

import { describe, expect, it, vi } from "vitest";

import { dispatchModule, fetchTaskList } from "../api-client";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("api-client", () => {
  it("fetchTaskList calls GET /tasklist", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ modules: ["github", "twitter"] }),
    });
    const result = await fetchTaskList();
    expect(result.modules).toEqual(["github", "twitter"]);
  });

  it("dispatchModule calls POST /<module>", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          module: "github",
          task: "uuid-123",
          param: "john",
          from_m: "Initial",
        }),
    });
    const result = await dispatchModule("github", {
      username: "john",
      from: "Initial",
    });
    expect(result.task).toBe("uuid-123");
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });
    await expect(fetchTaskList()).rejects.toThrow("API error 500");
  });
});

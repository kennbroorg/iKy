import { beforeEach, describe, expect, it } from "vitest";

import { useGatherStore } from "../gather-store";

describe("gatherStore", () => {
  beforeEach(() => useGatherStore.getState().reset());

  it("detects email input type", () => {
    useGatherStore.getState().setInput("test@example.com");
    expect(useGatherStore.getState().inputType).toBe("email");
  });

  it("detects username input type", () => {
    useGatherStore.getState().setInput("johndoe");
    expect(useGatherStore.getState().inputType).toBe("username");
  });

  it("tracks task dispatch", () => {
    useGatherStore.getState().setTaskDispatched("github", "uuid-1");
    const task = useGatherStore.getState().tasks.github;
    expect(task.taskId).toBe("uuid-1");
    expect(task.status).toBe("dispatching");
  });
});

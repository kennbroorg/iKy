import { useCallback } from "react";

import {
  dispatchModule,
  fetchTaskResult,
  fetchTaskState,
} from "@/lib/api-client";
import { parseModuleResult } from "@/lib/result-parser";
import { subscribeToTask } from "@/lib/socket-client";
import { useGatherStore } from "@/stores/gather-store";

export function useModuleDispatch() {
  const { setTaskDispatched, setTaskStatus, setTaskResult, setTaskError } =
    useGatherStore();

  const dispatch = useCallback(
    async (
      module: string,
      params: { username: string; from?: string; [key: string]: unknown },
    ) => {
      try {
        setTaskDispatched(module, "");
        const response = await dispatchModule(module, params);
        const { task: taskId } = response;
        setTaskDispatched(module, taskId);
        setTaskStatus(module, "pending");

        const cleanup = subscribeToTask(
          taskId,
          (data) =>
            setTaskStatus(
              module,
              data.state === "SUCCESS" ? "success" : "running",
            ),
          async (data) => {
            const parsed = parseModuleResult(
              data.result as Record<string, unknown>[],
            );
            setTaskResult(module, parsed);
            cleanup();
          },
          (data) => {
            setTaskError(module, data.error);
            cleanup();
          },
        );

        // HTTP polling fallback
        const pollResult = async () => {
          const maxAttempts = 120;
          for (let i = 0; i < maxAttempts; i++) {
            const currentTask = useGatherStore.getState().tasks[module];
            if (
              currentTask?.status === "success" ||
              currentTask?.status === "error"
            ) {
              return;
            }
            try {
              const state = await fetchTaskState(taskId, module);
              if (state.state === "SUCCESS") {
                const result = await fetchTaskResult(taskId);
                const parsed = parseModuleResult(result.result);
                setTaskResult(module, parsed);
                cleanup();
                return;
              }
              if (state.state === "FAILURE") {
                setTaskError(module, "Task failed");
                cleanup();
                return;
              }
            } catch {
              // continue polling
            }
            await new Promise((r) => setTimeout(r, 1000));
          }
          setTaskError(module, "Task timed out");
          cleanup();
        };

        pollResult();
      } catch (err) {
        setTaskError(
          module,
          err instanceof Error ? err.message : "Unknown error",
        );
      }
    },
    [setTaskDispatched, setTaskStatus, setTaskResult, setTaskError],
  );

  return { dispatch };
}

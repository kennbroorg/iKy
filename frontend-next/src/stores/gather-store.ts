import { create } from "zustand";

import type { ModuleResultRaw } from "@/types/api";

export type TaskStatus =
  | "idle"
  | "dispatching"
  | "pending"
  | "running"
  | "success"
  | "error";

export interface TaskEntry {
  taskId: string;
  status: TaskStatus;
  result?: ModuleResultRaw;
  error?: string;
}

interface GatherState {
  input: string;
  inputType: "email" | "username";
  tasks: Record<string, TaskEntry>;
  isSearching: boolean;
  setInput: (input: string) => void;
  startSearch: (input: string) => void;
  setTaskDispatched: (module: string, taskId: string) => void;
  setTaskStatus: (module: string, status: TaskStatus) => void;
  setTaskResult: (module: string, result: ModuleResultRaw) => void;
  setTaskError: (module: string, error: string) => void;
  reset: () => void;
}

const isEmail = (s: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);

export const useGatherStore = create<GatherState>((set) => ({
  input: "",
  inputType: "email",
  tasks: {},
  isSearching: false,

  setInput: (input) =>
    set({ input, inputType: isEmail(input) ? "email" : "username" }),

  startSearch: (input) =>
    set({
      input,
      inputType: isEmail(input) ? "email" : "username",
      tasks: {},
      isSearching: true,
    }),

  setTaskDispatched: (module, taskId) =>
    set((state) => ({
      tasks: {
        ...state.tasks,
        [module]: { taskId, status: "dispatching" },
      },
    })),

  setTaskStatus: (module, status) =>
    set((state) => ({
      tasks: {
        ...state.tasks,
        [module]: { ...state.tasks[module], status },
      },
    })),

  setTaskResult: (module, result) =>
    set((state) => ({
      tasks: {
        ...state.tasks,
        [module]: { ...state.tasks[module], status: "success", result },
      },
    })),

  setTaskError: (module, error) =>
    set((state) => ({
      tasks: {
        ...state.tasks,
        [module]: { ...state.tasks[module], status: "error", error },
      },
    })),

  reset: () => set({ input: "", tasks: {}, isSearching: false }),
}));

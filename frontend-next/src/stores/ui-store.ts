import { create } from "zustand";

import type { ModuleCategory } from "@/types/modules";

interface UiState {
  sidebarOpen: boolean;
  activeFilter: ModuleCategory | "all";
  toggleSidebar: () => void;
  setFilter: (filter: ModuleCategory | "all") => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  activeFilter: "all",
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setFilter: (activeFilter) => set({ activeFilter }),
}));

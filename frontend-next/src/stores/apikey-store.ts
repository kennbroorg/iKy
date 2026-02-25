import { create } from "zustand";

import type { ApiKey } from "@/types/api";

interface ApiKeyState {
  keys: ApiKey[];
  isLoading: boolean;
  setKeys: (keys: ApiKey[]) => void;
  addKey: (key: ApiKey) => void;
  updateKey: (id: string, updates: Partial<ApiKey>) => void;
  removeKey: (id: string) => void;
  setLoading: (loading: boolean) => void;
}

export const useApiKeyStore = create<ApiKeyState>((set) => ({
  keys: [],
  isLoading: false,
  setKeys: (keys) => set({ keys }),
  addKey: (key) => set((s) => ({ keys: [...s.keys, key] })),
  updateKey: (id, updates) =>
    set((s) => ({
      keys: s.keys.map((k) => (k.id === id ? { ...k, ...updates } : k)),
    })),
  removeKey: (id) => set((s) => ({ keys: s.keys.filter((k) => k.id !== id) })),
  setLoading: (isLoading) => set({ isLoading }),
}));

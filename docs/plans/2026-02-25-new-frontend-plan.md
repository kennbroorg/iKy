# New Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a new React frontend (`frontend-next/`) with usability parity to the existing Angular 8 frontend, using modern tooling, dark hacker aesthetic, and WebSocket support.

**Architecture:** React 19 + Vite 6 SPA talking to the existing Flask backend. Zustand for local state, TanStack Query for server state, Socket.IO for real-time task updates. Data-driven module registry with generic visualization components + custom overrides for unique modules.

**Tech Stack:** React 19, TypeScript, Vite 6, Tailwind CSS 4, shadcn/ui, Zustand, TanStack Query, Socket.IO, Recharts, react-force-graph-2d, react-leaflet, TanStack Table, Vitest, Playwright, MSW.

**Design Doc:** `docs/plans/2026-02-25-new-frontend-design.md`

---

## Phase 1: Project Scaffold

### Task 1.1: Initialize Vite + React + TypeScript project

**Files:**
- Create: `frontend-next/` (entire scaffold)

**Step 1: Create Vite project**

```bash
cd /home/jpdborgna/src/iKy
npm create vite@latest frontend-next -- --template react-ts
```

**Step 2: Verify it runs**

```bash
cd frontend-next && npm install && npm run dev -- --port 5173
```

Expected: Dev server on http://localhost:5173 with Vite + React boilerplate.

**Step 3: Clean up boilerplate**

Remove `src/App.css`, `src/assets/react.svg`, default content from `src/App.tsx` and `src/index.css`. Keep the skeleton.

**Step 4: Commit**

```bash
git add frontend-next/
git commit -m "[ADD] Scaffold frontend-next with Vite + React + TypeScript"
```

---

### Task 1.2: Install and configure Tailwind CSS 4

**Files:**
- Modify: `frontend-next/package.json`
- Create: `frontend-next/src/index.css` (Tailwind directives)

**Step 1: Install Tailwind**

```bash
cd frontend-next
npm install tailwindcss @tailwindcss/vite
```

**Step 2: Configure Vite plugin**

In `frontend-next/vite.config.ts`:
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173 },
});
```

**Step 3: Add Tailwind import to CSS**

In `frontend-next/src/index.css`:
```css
@import "tailwindcss";
```

**Step 4: Add path aliases to tsconfig**

In `frontend-next/tsconfig.json`, add to `compilerOptions`:
```json
{
  "baseUrl": ".",
  "paths": {
    "@/*": ["./src/*"]
  }
}
```

And install the Vite path plugin:
```bash
npm install -D @types/node
```

Update `vite.config.ts` to add path resolve:
```typescript
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: { port: 5173 },
});
```

**Step 5: Verify Tailwind works**

Add `<h1 className="text-3xl font-bold text-cyan-400">iKy</h1>` to App.tsx, confirm cyan text renders.

**Step 6: Commit**

```bash
git add -A && git commit -m "[ADD] Configure Tailwind CSS 4 with path aliases"
```

---

### Task 1.3: Initialize shadcn/ui

**Files:**
- Create: `frontend-next/components.json`
- Create: `frontend-next/src/components/ui/` (generated components)
- Modify: `frontend-next/src/index.css` (CSS variables)

**Step 1: Run shadcn init**

```bash
cd frontend-next
npx shadcn@latest init
```

Choose: TypeScript, New York style, Zinc base color, CSS variables = yes.

**Step 2: Configure dark theme CSS variables**

Override the generated CSS variables in `src/index.css` with iKy dark hacker theme:

```css
@layer base {
  :root {
    /* Dark-only theme - no light mode */
    --background: 240 10% 3.9%;      /* #0a0a0f near-black with blue tint */
    --foreground: 0 0% 95%;
    --card: 240 6% 7%;               /* #111118 dark gray */
    --card-foreground: 0 0% 95%;
    --popover: 240 6% 7%;
    --popover-foreground: 0 0% 95%;
    --primary: 187 92% 41%;          /* #06b6d4 cyan/teal accent */
    --primary-foreground: 240 10% 3.9%;
    --secondary: 240 4% 16%;
    --secondary-foreground: 0 0% 95%;
    --muted: 240 4% 16%;
    --muted-foreground: 240 5% 64%;
    --accent: 187 92% 41%;
    --accent-foreground: 240 10% 3.9%;
    --destructive: 0 62% 50%;
    --destructive-foreground: 0 0% 95%;
    --border: 240 4% 16%;
    --input: 240 4% 16%;
    --ring: 187 92% 41%;
  }
}
```

**Step 3: Install JetBrains Mono and Inter fonts**

```bash
npm install @fontsource/jetbrains-mono @fontsource/inter
```

Import in `src/main.tsx`:
```typescript
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
```

**Step 4: Install first shadcn components**

```bash
npx shadcn@latest add button card badge input tabs dialog toast sonner
```

**Step 5: Verify with a dark-themed card**

Render a `<Card>` with dark background, cyan border glow, and verify it looks right.

**Step 6: Commit**

```bash
git add -A && git commit -m "[ADD] Configure shadcn/ui with dark hacker theme"
```

---

## Phase 2: Core Infrastructure

### Task 2.1: TypeScript types for API contract

**Files:**
- Create: `frontend-next/src/types/api.ts`
- Create: `frontend-next/src/types/modules.ts`

**Step 1: Define API response types**

```typescript
// src/types/api.ts

/** Response from POST /<module> */
export interface TaskDispatchResponse {
  module: string;
  task: string; // UUID
  param: string;
  from_m: string;
}

/** Response from GET /state/<task_id>/<module> */
export interface TaskStateResponse {
  state: "PENDING" | "STARTED" | "SUCCESS" | "FAILURE" | "RETRY" | "REVOKED";
  task_id: string;
  task_app: string;
}

/** Individual result array items (order-dependent from backend) */
export interface ModuleResultRaw {
  module: string;
  param: string;
  validation: "hard" | "soft" | "no" | "not_used";
  raw: Record<string, unknown> | RawError[];
  graphic: GraphicItem[];
  profile: ProfileItem[];
  timeline: TimelineEvent[];
  tasks: TaskReference[];
}

export interface RawError {
  status: "Warning" | "Fail";
  reason: string;
  traceback?: string;
}

export interface GraphicItem {
  details?: unknown[];
  social?: unknown[];
  cal_actual?: string;
  cal_previous?: string;
  [key: string]: unknown;
}

export interface ProfileItem {
  email?: string;
  name?: string;
  organization?: string;
  location?: string;
  geo?: { lat: number; lng: number };
  photos?: { src: string; caption?: string }[];
  presence?: { source: string; url: string; name?: string }[];
  social?: { source: string; url: string; name?: string }[];
  [key: string]: unknown;
}

export interface TimelineEvent {
  date: string;
  action: string;
  icon?: string;
  desc?: string;
}

export interface TaskReference {
  module: string;
  param: string;
}

/** Response from GET /result/<task_id> */
export interface TaskResultResponse {
  result: Record<string, unknown>[];
  error?: string;
}

/** API Key */
export interface ApiKey {
  id: string;
  name: string;
  key: string;
}

/** Response from GET/POST /apikey */
export interface ApiKeyResponse {
  keys: ApiKey[];
}

/** Response from GET /tasklist */
export interface TaskListResponse {
  modules: string[];
}
```

**Step 2: Define module registry types**

```typescript
// src/types/modules.ts
import type { ComponentType } from "react";

export type ModuleCategory =
  | "social"
  | "email"
  | "search"
  | "leak"
  | "enrichment"
  | "username";

export type InputType = "email" | "username" | "both";

export interface ModuleConfig {
  id: string;
  label: string;
  icon: string; // lucide icon name or react-icons identifier
  category: ModuleCategory;
  inputType: InputType; // what kind of input this module accepts
  requiresApiKey?: string;
  specialParams?: Record<string, unknown>;
  visualization: {
    useGenericGraph?: boolean;
    useGenericChart?: boolean;
    useGenericTable?: boolean;
    customComponent?: ComponentType<{ data: unknown }>;
  };
}
```

**Step 3: Commit**

```bash
git add -A && git commit -m "[ADD] TypeScript types for API contract and module registry"
```

---

### Task 2.2: API client with environment config

**Files:**
- Create: `frontend-next/src/lib/api-client.ts`
- Create: `frontend-next/.env`
- Create: `frontend-next/.env.example`

**Step 1: Create environment files**

```env
# .env
VITE_API_URL=http://localhost:5000
VITE_WS_URL=ws://localhost:5000
```

```env
# .env.example
VITE_API_URL=http://localhost:5000
VITE_WS_URL=ws://localhost:5000
```

**Step 2: Create API client**

```typescript
// src/lib/api-client.ts
import type {
  ApiKey,
  ApiKeyResponse,
  TaskDispatchResponse,
  TaskListResponse,
  TaskResultResponse,
  TaskStateResponse,
} from "@/types/api";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/** GET /tasklist */
export function fetchTaskList(): Promise<TaskListResponse> {
  return request("/tasklist");
}

/** POST /<module> — dispatch a task */
export function dispatchModule(
  module: string,
  params: { username: string; from?: string; [key: string]: unknown }
): Promise<TaskDispatchResponse> {
  return request(`/${module}`, {
    method: "POST",
    body: JSON.stringify(params),
  });
}

/** GET /state/<task_id>/<module> — poll task state */
export function fetchTaskState(
  taskId: string,
  module: string
): Promise<TaskStateResponse> {
  return request(`/state/${taskId}/${module}`);
}

/** GET /result/<task_id> — fetch completed result */
export function fetchTaskResult(
  taskId: string
): Promise<TaskResultResponse> {
  return request(`/result/${taskId}`);
}

/** GET /apikey — read API keys (POST with empty body) */
export function fetchApiKeys(): Promise<ApiKeyResponse> {
  return request("/apikey", { method: "POST", body: JSON.stringify({}) });
}

/** POST /apikey — write API keys */
export function writeApiKeys(keys: ApiKey[]): Promise<ApiKeyResponse> {
  return request("/apikey", {
    method: "POST",
    body: JSON.stringify(keys),
  });
}
```

**Step 3: Write test for API client**

```typescript
// src/lib/__tests__/api-client.test.ts
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { fetchTaskList, dispatchModule } from "../api-client";

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("api-client", () => {
  beforeEach(() => mockFetch.mockClear());

  it("fetchTaskList calls GET /tasklist", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ modules: ["github", "twitter"] }),
    });
    const result = await fetchTaskList();
    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:5000/tasklist",
      expect.objectContaining({ headers: { "Content-Type": "application/json" } })
    );
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
```

**Step 4: Install Vitest and run test**

```bash
cd frontend-next
npm install -D vitest
```

Add to `package.json` scripts: `"test": "vitest run", "test:watch": "vitest"`

Run: `npx vitest run src/lib/__tests__/api-client.test.ts`
Expected: 3 tests PASS

**Step 5: Commit**

```bash
git add -A && git commit -m "[ADD] API client with typed endpoints and unit tests"
```

---

### Task 2.3: Zustand stores

**Files:**
- Create: `frontend-next/src/stores/gather-store.ts`
- Create: `frontend-next/src/stores/apikey-store.ts`
- Create: `frontend-next/src/stores/ui-store.ts`

**Step 1: Install Zustand**

```bash
npm install zustand
```

**Step 2: Create gather store**

```typescript
// src/stores/gather-store.ts
import { create } from "zustand";
import type { ModuleResultRaw } from "@/types/api";

type TaskStatus = "idle" | "dispatching" | "pending" | "running" | "success" | "error";

interface TaskEntry {
  taskId: string;
  status: TaskStatus;
  result?: ModuleResultRaw;
  error?: string;
}

interface GatherState {
  input: string;
  inputType: "email" | "username";
  tasks: Record<string, TaskEntry>; // keyed by module id
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
```

**Step 3: Create API key store**

```typescript
// src/stores/apikey-store.ts
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
```

**Step 4: Create UI store**

```typescript
// src/stores/ui-store.ts
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
```

**Step 5: Write store tests**

```typescript
// src/stores/__tests__/gather-store.test.ts
import { describe, expect, it, beforeEach } from "vitest";
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
```

**Step 6: Run tests**

Run: `npx vitest run src/stores/__tests__/`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add -A && git commit -m "[ADD] Zustand stores for gather, apikeys, and UI state"
```

---

### Task 2.4: Module registry

**Files:**
- Create: `frontend-next/src/lib/module-registry.ts`

**Step 1: Create module registry with all 28+ modules**

```typescript
// src/lib/module-registry.ts
import type { ModuleConfig } from "@/types/modules";

export const MODULE_REGISTRY: ModuleConfig[] = [
  // === Email/Leak ===
  {
    id: "emailrep",
    label: "EmailRep",
    icon: "mail-check",
    category: "email",
    inputType: "email",
    requiresApiKey: "emailrep_key",
    visualization: { useGenericChart: true, useGenericTable: true },
  },
  {
    id: "leaklookup",
    label: "LeakLookup",
    icon: "shield-alert",
    category: "leak",
    inputType: "email",
    visualization: { useGenericTable: true },
  },
  {
    id: "leaks",
    label: "HIBP",
    icon: "lock-keyhole",
    category: "leak",
    inputType: "email",
    requiresApiKey: "haveibeenpwned_key",
    visualization: { useGenericTable: true },
  },
  {
    id: "darkpass",
    label: "Darkpass",
    icon: "skull",
    category: "leak",
    inputType: "email",
    visualization: { useGenericTable: true },
  },
  {
    id: "psbdmp",
    label: "PsbDmp",
    icon: "file-text",
    category: "leak",
    inputType: "email",
    visualization: { useGenericTable: true },
  },
  {
    id: "holehe",
    label: "Holehe",
    icon: "user-search",
    category: "username",
    inputType: "email",
    visualization: { useGenericTable: true },
  },
  // === Social ===
  {
    id: "github",
    label: "GitHub",
    icon: "github",
    category: "social",
    inputType: "username",
    visualization: { useGenericGraph: true, useGenericTable: true },
  },
  {
    id: "gitlab",
    label: "GitLab",
    icon: "gitlab",
    category: "social",
    inputType: "username",
    visualization: { useGenericGraph: true, useGenericTable: true },
  },
  {
    id: "twitter",
    label: "Twitter",
    icon: "twitter",
    category: "social",
    inputType: "username",
    visualization: { useGenericGraph: true, useGenericChart: true },
  },
  {
    id: "instagram",
    label: "Instagram",
    icon: "instagram",
    category: "social",
    inputType: "username",
    visualization: { useGenericGraph: true, useGenericChart: true },
  },
  {
    id: "tiktok",
    label: "TikTok",
    icon: "music",
    category: "social",
    inputType: "username",
    visualization: { useGenericChart: true, useGenericTable: true },
  },
  {
    id: "reddit",
    label: "Reddit",
    icon: "message-circle",
    category: "social",
    inputType: "username",
    visualization: { useGenericGraph: true, useGenericTable: true },
  },
  {
    id: "mastodon",
    label: "Mastodon",
    icon: "at-sign",
    category: "social",
    inputType: "username",
    visualization: { useGenericChart: true, useGenericTable: true },
  },
  {
    id: "twitch",
    label: "Twitch",
    icon: "tv",
    category: "social",
    inputType: "username",
    visualization: { useGenericChart: true },
  },
  {
    id: "spotify",
    label: "Spotify",
    icon: "headphones",
    category: "social",
    inputType: "username",
    specialParams: { proc: 1 },
    visualization: { useGenericChart: true, useGenericTable: true },
  },
  {
    id: "tinder",
    label: "Tinder",
    icon: "flame",
    category: "social",
    inputType: "username",
    visualization: { useGenericTable: true },
  },
  {
    id: "venmo",
    label: "Venmo",
    icon: "dollar-sign",
    category: "social",
    inputType: "username",
    visualization: { useGenericGraph: true, useGenericTable: true },
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    icon: "briefcase",
    category: "social",
    inputType: "username",
    visualization: { useGenericGraph: true, useGenericTable: true },
  },
  {
    id: "keybase",
    label: "Keybase",
    icon: "key",
    category: "social",
    inputType: "username",
    visualization: { useGenericGraph: true, useGenericTable: true },
  },
  {
    id: "skype",
    label: "Skype",
    icon: "phone",
    category: "social",
    inputType: "username",
    visualization: { useGenericTable: true },
  },
  // === Username Search ===
  {
    id: "usersearch",
    label: "UserSearch",
    icon: "search",
    category: "username",
    inputType: "username",
    visualization: { useGenericTable: true },
  },
  {
    id: "socialscan",
    label: "SocialScan",
    icon: "scan",
    category: "username",
    inputType: "email",
    visualization: { useGenericTable: true },
  },
  {
    id: "sherlock",
    label: "Sherlock",
    icon: "fingerprint",
    category: "username",
    inputType: "username",
    visualization: { useGenericTable: true },
  },
  // === Search ===
  {
    id: "search",
    label: "Searchers",
    icon: "globe",
    category: "search",
    inputType: "username",
    visualization: { useGenericTable: true },
  },
  {
    id: "dorks",
    label: "Dorks",
    icon: "terminal",
    category: "search",
    inputType: "username",
    specialParams: { dorks: "" },
    visualization: { useGenericTable: true },
  },
  // === Enrichment ===
  {
    id: "peopledatalabs",
    label: "PeopleDataLabs",
    icon: "database",
    category: "enrichment",
    inputType: "email",
    requiresApiKey: "peopledatalabs_key",
    visualization: { useGenericTable: true },
  },
  {
    id: "fullcontact",
    label: "FullContact",
    icon: "contact",
    category: "enrichment",
    inputType: "email",
    requiresApiKey: "fullcontact_key",
    visualization: { useGenericTable: true },
  },
  {
    id: "ghostproject",
    label: "GhostProject",
    icon: "ghost",
    category: "enrichment",
    inputType: "email",
    visualization: { useGenericTable: true },
  },
];

/** Get modules by category */
export function getModulesByCategory(category: string): ModuleConfig[] {
  if (category === "all") return MODULE_REGISTRY;
  return MODULE_REGISTRY.filter((m) => m.category === category);
}

/** Get a single module config */
export function getModule(id: string): ModuleConfig | undefined {
  return MODULE_REGISTRY.find((m) => m.id === id);
}

/** Get modules applicable for a given input type */
export function getModulesForInput(
  input: string
): ModuleConfig[] {
  const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input);
  return MODULE_REGISTRY.filter(
    (m) => m.inputType === "both" || (isEmail ? m.inputType === "email" : m.inputType === "username")
  );
}
```

**Step 2: Write tests**

```typescript
// src/lib/__tests__/module-registry.test.ts
import { describe, expect, it } from "vitest";
import {
  MODULE_REGISTRY,
  getModulesByCategory,
  getModule,
  getModulesForInput,
} from "../module-registry";

describe("module-registry", () => {
  it("has 28 modules", () => {
    expect(MODULE_REGISTRY.length).toBe(28);
  });

  it("filters by category", () => {
    const leaks = getModulesByCategory("leak");
    expect(leaks.every((m) => m.category === "leak")).toBe(true);
    expect(leaks.length).toBeGreaterThan(0);
  });

  it("finds module by id", () => {
    const github = getModule("github");
    expect(github?.label).toBe("GitHub");
  });

  it("filters email modules for email input", () => {
    const mods = getModulesForInput("test@example.com");
    expect(mods.every((m) => m.inputType === "email" || m.inputType === "both")).toBe(true);
  });

  it("filters username modules for username input", () => {
    const mods = getModulesForInput("johndoe");
    expect(mods.every((m) => m.inputType === "username" || m.inputType === "both")).toBe(true);
  });
});
```

**Step 3: Run tests**

Run: `npx vitest run src/lib/__tests__/module-registry.test.ts`
Expected: All PASS

**Step 4: Commit**

```bash
git add -A && git commit -m "[ADD] Module registry with 28 OSINT modules and category filtering"
```

---

### Task 2.5: Socket.IO client

**Files:**
- Create: `frontend-next/src/lib/socket-client.ts`

**Step 1: Install Socket.IO client**

```bash
npm install socket.io-client
```

**Step 2: Create socket client**

```typescript
// src/lib/socket-client.ts
import { io, Socket } from "socket.io-client";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:5000";

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    socket = io(WS_URL, {
      autoConnect: false,
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });
  }
  return socket;
}

export function connectSocket(): void {
  const s = getSocket();
  if (!s.connected) s.connect();
}

export function disconnectSocket(): void {
  if (socket?.connected) socket.disconnect();
}

/** Subscribe to task updates for a specific task */
export function subscribeToTask(
  taskId: string,
  onState: (data: { task_id: string; module: string; state: string }) => void,
  onResult: (data: { task_id: string; module: string; result: unknown[] }) => void,
  onError: (data: { task_id: string; module: string; error: string }) => void
): () => void {
  const s = getSocket();
  const stateEvent = `task:state:${taskId}`;
  const resultEvent = `task:result:${taskId}`;
  const errorEvent = `task:error:${taskId}`;

  s.on(stateEvent, onState);
  s.on(resultEvent, onResult);
  s.on(errorEvent, onError);

  // Return cleanup function
  return () => {
    s.off(stateEvent, onState);
    s.off(resultEvent, onResult);
    s.off(errorEvent, onError);
  };
}
```

**Step 3: Commit**

```bash
git add -A && git commit -m "[ADD] Socket.IO client with task subscription support"
```

---

### Task 2.6: TanStack Query setup with module query hook

**Files:**
- Create: `frontend-next/src/hooks/use-module-query.ts`
- Modify: `frontend-next/src/app/` (add QueryClientProvider)

**Step 1: Install TanStack Query**

```bash
npm install @tanstack/react-query
```

**Step 2: Create QueryClient provider**

In `src/app/providers.tsx`:
```typescript
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 2,
    },
  },
});

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

**Step 3: Create the module query hook**

This is the core hook that handles dispatching a module task, polling for state, and fetching results. It uses TanStack Query's polling capabilities with Socket.IO as the primary path and HTTP polling as fallback.

```typescript
// src/hooks/use-module-query.ts
import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  dispatchModule,
  fetchTaskResult,
  fetchTaskState,
} from "@/lib/api-client";
import { subscribeToTask } from "@/lib/socket-client";
import { useGatherStore } from "@/stores/gather-store";
import { parseModuleResult } from "@/lib/result-parser";

export function useModuleDispatch() {
  const queryClient = useQueryClient();
  const {
    setTaskDispatched,
    setTaskStatus,
    setTaskResult,
    setTaskError,
  } = useGatherStore();

  const dispatch = useCallback(
    async (
      module: string,
      params: { username: string; from?: string; [key: string]: unknown }
    ) => {
      try {
        // 1. Dispatch task
        setTaskDispatched(module, "");
        const response = await dispatchModule(module, params);
        const { task: taskId } = response;
        setTaskDispatched(module, taskId);
        setTaskStatus(module, "pending");

        // 2. Try WebSocket subscription
        const cleanup = subscribeToTask(
          taskId,
          (data) => setTaskStatus(module, data.state === "SUCCESS" ? "success" : "running"),
          async (data) => {
            const parsed = parseModuleResult(data.result as Record<string, unknown>[]);
            setTaskResult(module, parsed);
            cleanup();
          },
          (data) => {
            setTaskError(module, data.error);
            cleanup();
          }
        );

        // 3. Fallback: HTTP polling (runs regardless, socket events will arrive first if available)
        const pollResult = async () => {
          const maxAttempts = 120; // 120 * 1s = 2 min timeout
          for (let i = 0; i < maxAttempts; i++) {
            const currentTask = useGatherStore.getState().tasks[module];
            if (currentTask?.status === "success" || currentTask?.status === "error") {
              return; // Socket already delivered the result
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
              // Polling error — continue trying
            }
            await new Promise((r) => setTimeout(r, 1000));
          }
          setTaskError(module, "Task timed out");
          cleanup();
        };

        pollResult();
      } catch (err) {
        setTaskError(module, err instanceof Error ? err.message : "Unknown error");
      }
    },
    [queryClient, setTaskDispatched, setTaskStatus, setTaskResult, setTaskError]
  );

  return { dispatch };
}
```

**Step 4: Create result parser**

The backend returns results as an array of single-key objects. Parse them into a typed shape.

```typescript
// src/lib/result-parser.ts
import type { ModuleResultRaw } from "@/types/api";

/** Parse the backend result array into a typed object */
export function parseModuleResult(
  resultArray: Record<string, unknown>[]
): ModuleResultRaw {
  const findValue = (key: string) =>
    resultArray.find((item) => key in item)?.[key];

  return {
    module: (findValue("module") as string) ?? "",
    param: (findValue("param") as string) ?? "",
    validation: (findValue("validation") as ModuleResultRaw["validation"]) ?? "not_used",
    raw: (findValue("raw") as Record<string, unknown>) ?? {},
    graphic: (findValue("graphic") as ModuleResultRaw["graphic"]) ?? [],
    profile: (findValue("profile") as ModuleResultRaw["profile"]) ?? [],
    timeline: (findValue("timeline") as ModuleResultRaw["timeline"]) ?? [],
    tasks: (findValue("tasks") as ModuleResultRaw["tasks"]) ?? [],
  };
}
```

**Step 5: Write test for result parser**

```typescript
// src/lib/__tests__/result-parser.test.ts
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
```

**Step 6: Run tests**

Run: `npx vitest run src/lib/__tests__/result-parser.test.ts`
Expected: PASS

**Step 7: Commit**

```bash
git add -A && git commit -m "[ADD] TanStack Query setup, module dispatch hook, and result parser"
```

---

## Phase 3: Layout & Navigation

### Task 3.1: App shell with sidebar and routing

**Files:**
- Create: `frontend-next/src/app/layout.tsx`
- Create: `frontend-next/src/app/router.tsx`
- Create: `frontend-next/src/components/layout/sidebar.tsx`
- Create: `frontend-next/src/components/layout/header.tsx`
- Modify: `frontend-next/src/main.tsx`
- Modify: `frontend-next/src/App.tsx`

**Step 1: Install React Router**

```bash
npm install react-router
```

**Step 2: Create router config**

```typescript
// src/app/router.tsx
import { createBrowserRouter, Navigate } from "react-router";
import { AppLayout } from "./layout";

// Lazy-loaded pages
const GathererPage = React.lazy(() => import("@/pages/gatherer/page"));
const ProfilePage = React.lazy(() => import("@/pages/profile/page"));
const TimelinePage = React.lazy(() => import("@/pages/timeline/page"));
const ApiKeysPage = React.lazy(() => import("@/pages/apikeys/page"));

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/gatherer" replace /> },
      { path: "gatherer", element: <GathererPage /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "timeline", element: <TimelinePage /> },
      { path: "apikeys", element: <ApiKeysPage /> },
    ],
  },
]);
```

**Step 3: Create sidebar component**

Build a collapsible sidebar with nav links (Gatherer, Profile, Timeline, API Keys), iKy logo at top, and collapse toggle. Use shadcn `Button` for nav items with Lucide icons. Active route highlighted with cyan accent.

**Step 4: Create header component**

Minimal header with sidebar toggle button and iKy branding text.

**Step 5: Create layout component**

```typescript
// src/app/layout.tsx
import { Outlet, Suspense } from "react-router";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

export function AppLayout() {
  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <Suspense fallback={<div className="text-muted-foreground">Loading...</div>}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
```

**Step 6: Wire up main.tsx**

```typescript
// src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router";
import { Providers } from "./app/providers";
import { router } from "./app/router";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Providers>
      <RouterProvider router={router} />
    </Providers>
  </React.StrictMode>
);
```

**Step 7: Create placeholder pages**

Create minimal placeholder components for each page (just a title) so routing works:
- `src/pages/gatherer/page.tsx` — `export default function GathererPage() { return <h1>Gatherer</h1>; }`
- `src/pages/profile/page.tsx`
- `src/pages/timeline/page.tsx`
- `src/pages/apikeys/page.tsx`

**Step 8: Verify navigation works**

Start dev server, confirm sidebar renders with dark theme, links navigate between pages, active route is highlighted.

**Step 9: Commit**

```bash
git add -A && git commit -m "[ADD] App shell with sidebar navigation, routing, and placeholder pages"
```

---

## Phase 4: Gatherer Page (Core)

### Task 4.1: Search bar component

**Files:**
- Create: `frontend-next/src/components/layout/search-bar.tsx`

**Step 1: Build search bar**

A full-width search input in the header area with:
- Text input with placeholder "Enter email or username..."
- Auto-detection badge showing "email" or "username" based on input
- Submit button with search icon
- Validation: shows error state for empty input
- On submit: calls `gatherStore.startSearch(input)` and triggers module dispatch

Use shadcn `Input`, `Button`, `Badge`. Style with cyan focus ring on dark background.

**Step 2: Wire to gather store and dispatch hook**

On submit, the search bar should:
1. Call `startSearch(input)` to reset state
2. Get applicable modules via `getModulesForInput(input)`
3. Call `dispatch(module, { username, from: "Initial" })` for each module
4. For email input: split email, use full email for email modules, username part for username modules

**Step 3: Verify it renders correctly**

**Step 4: Commit**

```bash
git add -A && git commit -m "[ADD] Search bar component with auto-detection and module dispatch"
```

---

### Task 4.2: Module progress grid

**Files:**
- Create: `frontend-next/src/components/gatherer/module-grid.tsx`

**Step 1: Build module grid component**

A CSS grid of small cards, one per dispatched module, showing:
- Module icon (from registry)
- Module label
- Status indicator: spinner (pending/running), green check (success), red X (error), gray dash (idle)
- Uses `gatherStore.tasks` for status

Each card is a small `Card` component with the module icon and a `StatusBadge`.

**Step 2: Add category filter**

A row of shadcn `Tabs` above the grid: All | Social | Leaks | Search | Username | Enrichment.
Reads from `uiStore.activeFilter`, filters displayed modules.

**Step 3: Commit**

```bash
git add -A && git commit -m "[ADD] Module progress grid with status indicators and category filters"
```

---

### Task 4.3: Generic result card with sub-tabs

**Files:**
- Create: `frontend-next/src/components/gatherer/result-card.tsx`

**Step 1: Build expandable result card**

A collapsible card for each module that has completed results:
- Header: module icon + label + validation badge + expand/collapse toggle
- Body (when expanded): sub-tabs for different visualizations
  - "Details" tab — key findings from `graphic` data
  - "Table" tab — tabular data from `graphic.social` or `graphic.details`
  - "Raw" tab — raw JSON viewer (collapsible `<pre>` with syntax highlighting)
- Uses module registry to decide which tabs to show

**Step 2: Build JSON viewer sub-component**

Simple `<pre>` block with `JSON.stringify(data, null, 2)`, styled with JetBrains Mono font, dark background, overflow scroll.

**Step 3: Commit**

```bash
git add -A && git commit -m "[ADD] Generic result card with details/table/raw sub-tabs"
```

---

### Task 4.4: Assemble gatherer page

**Files:**
- Modify: `frontend-next/src/pages/gatherer/page.tsx`

**Step 1: Compose the gatherer page**

```typescript
export default function GathererPage() {
  return (
    <div className="space-y-6">
      <SearchBar />
      <ModuleGrid />
      <ResultCards />
    </div>
  );
}
```

Where `ResultCards` maps over `gatherStore.tasks` entries with status "success" and renders a `ResultCard` for each.

**Step 2: Add export button**

A "Export All JSON" button that serializes all results from `gatherStore.tasks` into a downloadable JSON file.

**Step 3: Verify end-to-end flow**

With backend running: type an email → modules dispatch → progress grid updates → result cards appear. (This requires the backend to be running.)

**Step 4: Commit**

```bash
git add -A && git commit -m "[ADD] Assemble gatherer page with search, grid, and result cards"
```

---

## Phase 5: Visualization Components

### Task 5.1: Force-directed graph component

**Files:**
- Create: `frontend-next/src/components/viz/force-graph.tsx`

**Step 1: Install react-force-graph**

```bash
npm install react-force-graph-2d
```

**Step 2: Build ForceGraph component**

A wrapper around `ForceGraph2D` that accepts `nodes` and `links` arrays from the module's `graphic` data. Dark background, cyan accent for nodes, gray links. Node labels rendered as text. Interactive: drag, zoom, hover tooltip.

Props: `{ nodes: { id: string; label: string; img?: string; group?: string }[]; links: { source: string; target: string }[] }`

**Step 3: Commit**

```bash
git add -A && git commit -m "[ADD] Force-directed graph visualization component"
```

---

### Task 5.2: Chart component (Recharts)

**Files:**
- Create: `frontend-next/src/components/viz/module-chart.tsx`

**Step 1: Install Recharts**

```bash
npm install recharts
```

**Step 2: Build ModuleChart component**

A flexible chart component that auto-selects chart type based on data shape:
- Bar chart for categorical data
- Pie chart for distribution data
- Line chart for time-series data

Props: `{ data: Record<string, unknown>[]; type?: "bar" | "pie" | "line" }`

Dark theme: dark background, cyan/teal bars, gray grid lines. Responsive via `ResponsiveContainer`.

**Step 3: Commit**

```bash
git add -A && git commit -m "[ADD] Recharts-based module chart component"
```

---

### Task 5.3: Data table component (TanStack Table)

**Files:**
- Create: `frontend-next/src/components/viz/data-table.tsx`

**Step 1: Install TanStack Table**

```bash
npm install @tanstack/react-table
```

**Step 2: Build DataTable component**

A generic table using TanStack Table with:
- Auto-generated columns from data keys
- Sorting per column
- Search/filter input
- Pagination
- Dark theme styling with shadcn table primitives

Props: `{ data: Record<string, unknown>[]; columns?: ColumnDef[] }`

**Step 3: Add shadcn table component**

```bash
npx shadcn@latest add table
```

**Step 4: Commit**

```bash
git add -A && git commit -m "[ADD] Generic data table with sorting, filtering, and pagination"
```

---

### Task 5.4: Location map component

**Files:**
- Create: `frontend-next/src/components/viz/location-map.tsx`

**Step 1: Install react-leaflet**

```bash
npm install react-leaflet leaflet
npm install -D @types/leaflet
```

**Step 2: Build LocationMap component**

Dark-themed Leaflet map with:
- Dark tile layer (CartoDB dark_all or similar)
- Markers for discovered locations
- Popup with location info on click

Props: `{ locations: { lat: number; lng: number; label: string }[] }`

**Step 3: Copy GeoJSON assets**

Copy `frontend/src/assets/leaflet-countries/` and `frontend/src/assets/map/` to `frontend-next/public/geo/`.

**Step 4: Commit**

```bash
git add -A && git commit -m "[ADD] Leaflet map component with dark tiles and location markers"
```

---

### Task 5.5: Word cloud component

**Files:**
- Create: `frontend-next/src/components/viz/word-cloud.tsx`

**Step 1: Install react-wordcloud**

```bash
npm install react-wordcloud
```

(If this package is unmaintained/broken, fall back to `d3-cloud` with a custom React wrapper.)

**Step 2: Build WordCloud component**

Props: `{ words: { text: string; value: number }[] }`

Cyan/teal color scheme on dark background.

**Step 3: Commit**

```bash
git add -A && git commit -m "[ADD] Word cloud visualization component"
```

---

## Phase 6: Profile Page

### Task 6.1: Profile data aggregation

**Files:**
- Create: `frontend-next/src/lib/profile-aggregator.ts`
- Create: `frontend-next/src/lib/__tests__/profile-aggregator.test.ts`

**Step 1: Write failing test**

```typescript
// src/lib/__tests__/profile-aggregator.test.ts
import { describe, expect, it } from "vitest";
import { aggregateProfile } from "../profile-aggregator";
import type { ModuleResultRaw } from "@/types/api";

describe("aggregateProfile", () => {
  it("merges profile data from multiple modules", () => {
    const results: Record<string, { result?: ModuleResultRaw }> = {
      github: {
        result: {
          module: "github", param: "john", validation: "no",
          raw: {}, graphic: [], tasks: [],
          profile: [{ name: "John Doe", organization: "ACME" }],
          timeline: [],
        },
      },
      twitter: {
        result: {
          module: "twitter", param: "john", validation: "no",
          raw: {}, graphic: [], tasks: [],
          profile: [{ name: "John D.", location: "NYC", photos: [{ src: "http://img.jpg" }] }],
          timeline: [],
        },
      },
    };
    const profile = aggregateProfile(results);
    expect(profile.names).toContain("John Doe");
    expect(profile.names).toContain("John D.");
    expect(profile.locations).toContain("NYC");
    expect(profile.photos).toHaveLength(1);
    expect(profile.organizations).toContain("ACME");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npx vitest run src/lib/__tests__/profile-aggregator.test.ts`
Expected: FAIL

**Step 3: Implement aggregator**

```typescript
// src/lib/profile-aggregator.ts
import type { ModuleResultRaw } from "@/types/api";

export interface AggregatedProfile {
  names: string[];
  emails: string[];
  organizations: string[];
  locations: string[];
  photos: { src: string; caption?: string; source: string }[];
  presence: { source: string; url: string; name?: string }[];
  social: { source: string; url: string; name?: string }[];
  geo: { lat: number; lng: number; label: string }[];
}

export function aggregateProfile(
  tasks: Record<string, { result?: ModuleResultRaw }>
): AggregatedProfile {
  const profile: AggregatedProfile = {
    names: [],
    emails: [],
    organizations: [],
    locations: [],
    photos: [],
    presence: [],
    social: [],
    geo: [],
  };

  for (const [moduleName, task] of Object.entries(tasks)) {
    if (!task.result?.profile) continue;
    for (const item of task.result.profile) {
      if (item.name && !profile.names.includes(item.name as string))
        profile.names.push(item.name as string);
      if (item.email && !profile.emails.includes(item.email as string))
        profile.emails.push(item.email as string);
      if (item.organization && !profile.organizations.includes(item.organization as string))
        profile.organizations.push(item.organization as string);
      if (item.location && !profile.locations.includes(item.location as string))
        profile.locations.push(item.location as string);
      if (item.photos) {
        for (const p of item.photos as { src: string; caption?: string }[]) {
          profile.photos.push({ ...p, source: moduleName });
        }
      }
      if (item.presence)
        profile.presence.push(
          ...(item.presence as { source: string; url: string }[])
        );
      if (item.social)
        profile.social.push(
          ...(item.social as { source: string; url: string }[])
        );
      if (item.geo) {
        const g = item.geo as { lat: number; lng: number };
        profile.geo.push({ ...g, label: moduleName });
      }
    }
  }

  return profile;
}
```

**Step 4: Run test to verify it passes**

Run: `npx vitest run src/lib/__tests__/profile-aggregator.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add -A && git commit -m "[ADD] Profile data aggregator with tests"
```

---

### Task 6.2: Profile page UI

**Files:**
- Modify: `frontend-next/src/pages/profile/page.tsx`

**Step 1: Build profile page**

Layout:
- **Header**: Avatar (first photo or placeholder), primary name, email, location
- **Tabs** (shadcn Tabs): Overview | Photos | Social | Map
- **Overview tab**: Cards showing key facts, organizations, presence list
- **Photos tab**: Responsive grid of discovered images
- **Social tab**: Cards for each social presence with platform icons and links
- **Map tab**: `LocationMap` component with all discovered geo coordinates

Reads from `gatherStore.tasks`, runs through `aggregateProfile()`.

**Step 2: Commit**

```bash
git add -A && git commit -m "[ADD] Profile page with overview, photos, social, and map tabs"
```

---

## Phase 7: Timeline Page

### Task 7.1: Timeline data aggregation and page

**Files:**
- Create: `frontend-next/src/lib/timeline-aggregator.ts`
- Modify: `frontend-next/src/pages/timeline/page.tsx`

**Step 1: Write failing test for timeline aggregator**

```typescript
// src/lib/__tests__/timeline-aggregator.test.ts
import { describe, expect, it } from "vitest";
import { aggregateTimeline } from "../timeline-aggregator";

describe("aggregateTimeline", () => {
  it("aggregates and sorts events from multiple modules newest-first", () => {
    const tasks = {
      github: {
        result: {
          module: "github", param: "john", validation: "no" as const,
          raw: {}, graphic: [], profile: [], tasks: [],
          timeline: [
            { date: "2024/01/15 10:30:00", action: "Created repo" },
            { date: "2023/06/01 00:00:00", action: "Joined GitHub" },
          ],
        },
      },
      twitter: {
        result: {
          module: "twitter", param: "john", validation: "no" as const,
          raw: {}, graphic: [], profile: [], tasks: [],
          timeline: [
            { date: "2024/03/20 15:00:00", action: "Posted tweet" },
          ],
        },
      },
    };
    const events = aggregateTimeline(tasks);
    expect(events).toHaveLength(3);
    expect(events[0].action).toBe("Posted tweet"); // newest first
    expect(events[0].source).toBe("twitter");
  });
});
```

**Step 2: Run test — expect FAIL**

**Step 3: Implement aggregator**

```typescript
// src/lib/timeline-aggregator.ts
import type { ModuleResultRaw, TimelineEvent } from "@/types/api";

export interface AggregatedTimelineEvent extends TimelineEvent {
  source: string;
}

export function aggregateTimeline(
  tasks: Record<string, { result?: ModuleResultRaw }>
): AggregatedTimelineEvent[] {
  const events: AggregatedTimelineEvent[] = [];

  for (const [moduleName, task] of Object.entries(tasks)) {
    if (!task.result?.timeline) continue;
    for (const event of task.result.timeline) {
      events.push({ ...event, source: moduleName });
    }
  }

  // Sort newest first
  events.sort((a, b) => {
    const dateA = new Date(a.date.replace(/\//g, "-"));
    const dateB = new Date(b.date.replace(/\//g, "-"));
    return dateB.getTime() - dateA.getTime();
  });

  return events;
}
```

**Step 4: Run test — expect PASS**

**Step 5: Build timeline page**

Vertical timeline layout with:
- Each event: colored dot (by module category), date, module badge, action text, optional description
- Module icon next to each event
- Alternating subtle backgrounds for readability
- Uses `aggregateTimeline(gatherStore.tasks)`

**Step 6: Commit**

```bash
git add -A && git commit -m "[ADD] Timeline page with data aggregation and vertical timeline UI"
```

---

## Phase 8: API Keys Page

### Task 8.1: API keys page with CRUD

**Files:**
- Modify: `frontend-next/src/pages/apikeys/page.tsx`
- Create: `frontend-next/src/hooks/use-api-keys.ts`

**Step 1: Create API keys hook**

```typescript
// src/hooks/use-api-keys.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchApiKeys, writeApiKeys } from "@/lib/api-client";
import { useApiKeyStore } from "@/stores/apikey-store";

export function useApiKeys() {
  const queryClient = useQueryClient();
  const { setKeys, setLoading } = useApiKeyStore();

  const query = useQuery({
    queryKey: ["apikeys"],
    queryFn: async () => {
      setLoading(true);
      const res = await fetchApiKeys();
      setKeys(res.keys);
      setLoading(false);
      return res.keys;
    },
  });

  const mutation = useMutation({
    mutationFn: writeApiKeys,
    onSuccess: (data) => {
      setKeys(data.keys);
      queryClient.invalidateQueries({ queryKey: ["apikeys"] });
    },
  });

  return { query, save: mutation.mutate, isSaving: mutation.isPending };
}
```

**Step 2: Build API keys page**

- Table with columns: Name, Key (masked with toggle reveal), Actions (edit, delete)
- Inline editing: click edit → row becomes editable
- Add row button
- Import/Export buttons:
  - Export: downloads keys as JSON file
  - Import: file picker, parses JSON, loads into table
- Save button calls `writeApiKeys()`

Use shadcn `Table`, `Input`, `Button`, `Dialog` for confirmation.

**Step 3: Commit**

```bash
git add -A && git commit -m "[ADD] API keys page with CRUD, import/export, and masked display"
```

---

## Phase 9: Backend WebSocket Support

### Task 9.1: Add flask-socketio to backend

**Files:**
- Modify: `requirements.txt` (add `flask-socketio`, `eventlet`)
- Modify: `backend/factories/application.py`
- Modify: `backend/api.py` (add socket emit after task result)
- Modify: `backend/run.py` (use socketio.run)

**Step 1: Add dependencies**

Add to `requirements.txt`:
```
flask-socketio==5.5.1
eventlet==0.39.1
```

**Step 2: Integrate SocketIO into Flask app factory**

```python
# backend/factories/application.py
import os

from api import home
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from .configuration import get_config

socketio = SocketIO()

def create_application() -> tuple[Flask, SocketIO]:
    config = get_config()
    app = Flask(__name__)
    cors_origins = os.environ.get(
        "CORS_ORIGINS", "http://localhost:4200,http://localhost:5173"
    ).split(",")
    CORS(app, origins=cors_origins)
    app.config.from_object(config)
    app.register_blueprint(home)
    socketio.init_app(
        app,
        cors_allowed_origins=cors_origins,
        message_queue=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        async_mode="eventlet",
    )
    return app, socketio
```

**Step 3: Add socket events to task result endpoint**

In `backend/api.py`, after fetching a result, emit to the task-specific channel:

```python
from flask_socketio import emit

@home.route("/result/<task_id>")
def r_result(task_id):
    celery = create_celery(current_app)
    try:
        res = celery.AsyncResult(task_id).get(timeout=120)
    except Exception:
        socketio.emit(f"task:error:{task_id}", {
            "task_id": task_id, "error": "Task timed out or failed"
        })
        return jsonify(error="Task timed out or failed"), 504

    socketio.emit(f"task:result:{task_id}", {
        "task_id": task_id, "result": res
    })
    return jsonify(result=res)
```

**Note:** This is a minimal approach. A more robust implementation would use Celery signals (`task_success`, `task_failure`) to emit socket events directly from the worker, bypassing the HTTP endpoint entirely. That can be added as a follow-up optimization.

**Step 4: Update run.py**

```python
from factories.application import create_application, socketio

app, sio = create_application()

if __name__ == "__main__":
    sio.run(app, host="0.0.0.0", port=5000, debug=True)
```

**Step 5: Verify existing tests still pass**

Run: `just test`
Expected: All backend tests pass (socketio shouldn't break existing HTTP endpoints).

**Step 6: Commit**

```bash
git add -A && git commit -m "[ADD] Flask-SocketIO integration for real-time task updates"
```

---

## Phase 10: Docker Integration

### Task 10.1: Create frontend-next Dockerfile and compose config

**Files:**
- Create: `install/docker/frontend-next/Dockerfile`
- Create: `install/docker/frontend-next/nginx.conf`
- Modify: `docker-compose.yml`

**Step 1: Create Dockerfile (multi-stage)**

```dockerfile
# install/docker/frontend-next/Dockerfile
FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY frontend-next/package*.json ./
RUN npm ci
COPY frontend-next/ .
ARG VITE_API_URL=http://localhost:5000
ARG VITE_WS_URL=ws://localhost:5000
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY install/docker/frontend-next/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5173
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:5173/ || exit 1
```

**Step 2: Create nginx.conf**

```nginx
server {
    listen 5173;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Step 3: Add to docker-compose.yml**

Add `frontend-next` service alongside existing services:

```yaml
frontend-next:
    build:
        context: .
        dockerfile: ./install/docker/frontend-next/Dockerfile
        args:
            VITE_API_URL: http://backend:5000
            VITE_WS_URL: ws://backend:5000
    ports:
        - "5173:5173"
    depends_on:
        - backend
```

**Step 4: Update backend CORS**

In `docker-compose.yml`, add environment variable to backend service:
```yaml
backend:
    environment:
        - CORS_ORIGINS=http://localhost:4200,http://localhost:5173,http://frontend-next:5173
```

**Step 5: Build and verify**

```bash
just build
just up
```

Visit http://localhost:5173 — new frontend should load.
Visit http://localhost:4200 — old frontend should still work.

**Step 6: Commit**

```bash
git add -A && git commit -m "[ADD] Docker setup for frontend-next with nginx and compose integration"
```

---

## Phase 11: Testing & Polish

### Task 11.1: MSW setup for dev/test API mocking

**Files:**
- Create: `frontend-next/src/mocks/handlers.ts`
- Create: `frontend-next/src/mocks/browser.ts`
- Create: `frontend-next/src/mocks/data.ts`

**Step 1: Install MSW**

```bash
npm install -D msw
npx msw init public/ --save
```

**Step 2: Create mock handlers**

Mock the main endpoints (`/tasklist`, `POST /<module>`, `/state/*`, `/result/*`, `/apikey`) with realistic sample data. This allows development without running the backend.

**Step 3: Create browser worker**

```typescript
// src/mocks/browser.ts
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);
```

**Step 4: Conditional activation in main.tsx**

```typescript
async function enableMocking() {
  if (import.meta.env.DEV && import.meta.env.VITE_ENABLE_MOCKS === "true") {
    const { worker } = await import("./mocks/browser");
    return worker.start();
  }
}

enableMocking().then(() => {
  // render app
});
```

**Step 5: Commit**

```bash
git add -A && git commit -m "[ADD] MSW mock service worker for development without backend"
```

---

### Task 11.2: Playwright e2e smoke test

**Files:**
- Create: `frontend-next/e2e/gatherer.spec.ts`
- Create: `frontend-next/playwright.config.ts`

**Step 1: Install Playwright**

```bash
npm install -D @playwright/test
npx playwright install chromium
```

**Step 2: Write smoke test**

```typescript
// e2e/gatherer.spec.ts
import { test, expect } from "@playwright/test";

test("search bar accepts input and shows module grid", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/gatherer/);
  const searchInput = page.getByPlaceholder(/email or username/i);
  await expect(searchInput).toBeVisible();
  await searchInput.fill("test@example.com");
  await expect(page.getByText(/email/i)).toBeVisible(); // auto-detect badge
});

test("sidebar navigation works", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /profile/i }).click();
  await expect(page).toHaveURL(/profile/);
  await page.getByRole("link", { name: /timeline/i }).click();
  await expect(page).toHaveURL(/timeline/);
  await page.getByRole("link", { name: /api keys/i }).click();
  await expect(page).toHaveURL(/apikeys/);
});
```

**Step 3: Add playwright config**

```typescript
// playwright.config.ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  webServer: {
    command: "npm run dev",
    port: 5173,
    reuseExistingServer: true,
  },
  use: {
    baseURL: "http://localhost:5173",
  },
});
```

**Step 4: Run tests**

```bash
npx playwright test
```

**Step 5: Commit**

```bash
git add -A && git commit -m "[ADD] Playwright e2e smoke tests for navigation and search"
```

---

### Task 11.3: Update justfile with frontend-next commands

**Files:**
- Modify: `justfile` (add new recipes)

**Step 1: Add recipes**

```just
# Frontend-next dev commands
dev-next:
    cd frontend-next && npm run dev

build-next:
    cd frontend-next && npm run build

test-next:
    cd frontend-next && npx vitest run

test-next-e2e:
    cd frontend-next && npx playwright test

lint-next:
    cd frontend-next && npx tsc --noEmit
```

**Step 2: Commit**

```bash
git add -A && git commit -m "[ADD] Justfile recipes for frontend-next dev commands"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1.1–1.3 | Project scaffold (Vite, Tailwind, shadcn) |
| 2 | 2.1–2.6 | Core infrastructure (types, API client, stores, registry, socket, queries) |
| 3 | 3.1 | Layout shell, sidebar, routing |
| 4 | 4.1–4.4 | Gatherer page (search, progress grid, result cards) |
| 5 | 5.1–5.5 | Visualization components (graph, chart, table, map, word cloud) |
| 6 | 6.1–6.2 | Profile page with data aggregation |
| 7 | 7.1 | Timeline page with aggregation |
| 8 | 8.1 | API keys page with CRUD |
| 9 | 9.1 | Backend WebSocket support |
| 10 | 10.1 | Docker integration |
| 11 | 11.1–11.3 | Testing (MSW, Playwright) and justfile |

**Total: ~22 tasks across 11 phases.**

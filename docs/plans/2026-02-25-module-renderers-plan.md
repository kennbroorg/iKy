# Module-Specific Renderers Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bring all 28 frontend-next modules to visualization parity with the original Angular frontend by implementing module-specific renderers that replace the generic ResultCard fallback.

**Architecture:** Module renderer registry pattern. Each module gets a custom React component that parses its `graphic[]` data at known positional indices and renders the appropriate visualizations. `ResultCard` checks the registry first; falls back to generic tabs if no renderer exists. Shared viz primitives (treemap, bubble chart, donut) are added to `src/components/viz/`.

**Tech Stack:** React 19, Recharts 3.7 (treemap, charts), d3-hierarchy (bubble chart), existing ForceGraph/WordCloud/LocationMap/DataTable components, Tailwind 4, shadcn/ui.

---

## Task 1: Add d3-hierarchy dependency

**Files:**
- Modify: `frontend-next/package.json`

**Step 1: Install d3-hierarchy for bubble chart circle-packing**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npm install d3-hierarchy @types/d3-hierarchy`

**Step 2: Verify installation**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && node -e "require('d3-hierarchy')"`
Expected: No error

**Step 3: Commit**

```bash
git add frontend-next/package.json frontend-next/package-lock.json
git commit -m "[ADD] d3-hierarchy dependency for bubble chart viz"
```

---

## Task 2: Create Treemap viz component

**Files:**
- Create: `frontend-next/src/components/viz/treemap-chart.tsx`
- Test: `frontend-next/src/lib/__tests__/treemap-chart.test.ts`

**Step 1: Write the test**

File: `frontend-next/src/lib/__tests__/treemap-chart.test.ts`

This is a data-transformation unit test since Recharts Treemap does the rendering.

```typescript
import { describe, expect, it } from "vitest";

// We'll test the data normalization utility that the Treemap component uses
import { normalizeTreemapData } from "@/components/viz/treemap-chart";

describe("normalizeTreemapData", () => {
  it("converts children array to recharts treemap format", () => {
    const input = [
      { name: "Following", total: 500 },
      { name: "Followers", total: 1200 },
      { name: "Tweets", total: 3400 },
      { name: "Likes", total: 8900 },
    ];
    const result = normalizeTreemapData(input);
    expect(result).toHaveLength(4);
    expect(result[0]).toEqual({ name: "Following", size: 500 });
    expect(result[1]).toEqual({ name: "Followers", size: 1200 });
  });

  it("handles empty input", () => {
    expect(normalizeTreemapData([])).toEqual([]);
  });

  it("handles value key instead of total", () => {
    const input = [
      { name: "A", value: 10 },
      { name: "B", value: 20 },
    ];
    const result = normalizeTreemapData(input);
    expect(result).toEqual([
      { name: "A", size: 10 },
      { name: "B", size: 20 },
    ]);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vitest run src/lib/__tests__/treemap-chart.test.ts`
Expected: FAIL — module not found

**Step 3: Implement treemap component**

File: `frontend-next/src/components/viz/treemap-chart.tsx`

```tsx
import { ResponsiveContainer, Treemap } from "recharts";

const TREEMAP_COLORS = [
  "#06b6d4", // cyan-500
  "#14b8a6", // teal-500
  "#0891b2", // cyan-600
  "#0d9488", // teal-600
  "#22d3ee", // cyan-400
  "#2dd4bf", // teal-400
] as const;

interface TreemapEntry {
  name: string;
  total?: number;
  value?: number;
  size?: number;
}

interface TreemapChartProps {
  data: TreemapEntry[];
  height?: number;
}

export function normalizeTreemapData(
  data: TreemapEntry[],
): { name: string; size: number }[] {
  return data.map((d) => ({
    name: d.name,
    size: d.total ?? d.value ?? d.size ?? 0,
  }));
}

function CustomContent(props: {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  size?: number;
  index?: number;
  depth?: number;
}) {
  const { x = 0, y = 0, width = 0, height = 0, name, size, index = 0, depth } = props;
  if (depth !== 1 || width < 30 || height < 20) return null;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={TREEMAP_COLORS[index % TREEMAP_COLORS.length]}
        stroke="rgba(10, 10, 15, 0.8)"
        strokeWidth={2}
        rx={4}
      />
      {width > 50 && height > 30 && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - 6}
            textAnchor="middle"
            fill="white"
            fontSize={12}
            fontWeight={600}
          >
            {name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 10}
            textAnchor="middle"
            fill="rgba(255,255,255,0.7)"
            fontSize={11}
          >
            {typeof size === "number" ? size.toLocaleString() : ""}
          </text>
        </>
      )}
    </g>
  );
}

export function TreemapChart({ data, height = 250 }: TreemapChartProps) {
  const normalized = normalizeTreemapData(data);
  if (normalized.length === 0) {
    return (
      <p className="text-sm italic text-muted-foreground">No data available.</p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <Treemap
        data={normalized}
        dataKey="size"
        nameKey="name"
        content={<CustomContent />}
      />
    </ResponsiveContainer>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vitest run src/lib/__tests__/treemap-chart.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-next/src/components/viz/treemap-chart.tsx frontend-next/src/lib/__tests__/treemap-chart.test.ts
git commit -m "[ADD] Treemap visualization component with Recharts"
```

---

## Task 3: Create BubbleChart viz component

**Files:**
- Create: `frontend-next/src/components/viz/bubble-chart.tsx`
- Test: `frontend-next/src/lib/__tests__/bubble-chart.test.ts`

**Step 1: Write the test**

File: `frontend-next/src/lib/__tests__/bubble-chart.test.ts`

```typescript
import { describe, expect, it } from "vitest";

import { computeBubbleLayout } from "@/components/viz/bubble-chart";

describe("computeBubbleLayout", () => {
  it("returns positioned circles from flat data", () => {
    const input = [
      { name: "JavaScript", value: 50 },
      { name: "Python", value: 30 },
      { name: "Rust", value: 20 },
    ];
    const circles = computeBubbleLayout(input, 400, 300);
    expect(circles).toHaveLength(3);
    for (const c of circles) {
      expect(c).toHaveProperty("x");
      expect(c).toHaveProperty("y");
      expect(c).toHaveProperty("r");
      expect(c).toHaveProperty("name");
      expect(c.r).toBeGreaterThan(0);
    }
  });

  it("sizes bubbles proportional to value", () => {
    const input = [
      { name: "Big", value: 100 },
      { name: "Small", value: 10 },
    ];
    const circles = computeBubbleLayout(input, 400, 300);
    const big = circles.find((c) => c.name === "Big")!;
    const small = circles.find((c) => c.name === "Small")!;
    expect(big.r).toBeGreaterThan(small.r);
  });

  it("handles empty input", () => {
    expect(computeBubbleLayout([], 400, 300)).toEqual([]);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vitest run src/lib/__tests__/bubble-chart.test.ts`
Expected: FAIL

**Step 3: Implement bubble chart component**

File: `frontend-next/src/components/viz/bubble-chart.tsx`

```tsx
import { useEffect, useRef, useState } from "react";

import { hierarchy, pack } from "d3-hierarchy";

const BUBBLE_COLORS = [
  "#06b6d4",
  "#14b8a6",
  "#22d3ee",
  "#2dd4bf",
  "#0891b2",
  "#0d9488",
  "#67e8f9",
  "#5eead4",
] as const;

interface BubbleEntry {
  name: string;
  value: number;
}

interface LayoutCircle {
  x: number;
  y: number;
  r: number;
  name: string;
  value: number;
}

interface BubbleChartProps {
  data: BubbleEntry[];
  height?: number;
}

export function computeBubbleLayout(
  data: BubbleEntry[],
  width: number,
  height: number,
): LayoutCircle[] {
  if (data.length === 0) return [];

  const root = hierarchy({ children: data } as {
    children: BubbleEntry[];
  })
    .sum((d) => ("value" in d ? (d as BubbleEntry).value : 0))
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  const packLayout = pack<{ children: BubbleEntry[] }>()
    .size([width, height])
    .padding(4);

  packLayout(root);

  return (root.leaves() as unknown as { x: number; y: number; r: number; data: BubbleEntry }[]).map(
    (leaf) => ({
      x: leaf.x,
      y: leaf.y,
      r: leaf.r,
      name: leaf.data.name,
      value: leaf.data.value,
    }),
  );
}

export function BubbleChart({ data, height = 300 }: BubbleChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(400);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (w && w > 0) setWidth(w);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const circles = computeBubbleLayout(data, width, height);

  if (circles.length === 0) {
    return (
      <p className="text-sm italic text-muted-foreground">No data available.</p>
    );
  }

  return (
    <div ref={containerRef} className="w-full">
      <svg width={width} height={height} className="overflow-visible">
        {circles.map((c, i) => (
          <g key={c.name}>
            <circle
              cx={c.x}
              cy={c.y}
              r={c.r}
              fill={BUBBLE_COLORS[i % BUBBLE_COLORS.length]}
              opacity={0.8}
              stroke={BUBBLE_COLORS[i % BUBBLE_COLORS.length]}
              strokeWidth={1}
            />
            {c.r > 20 && (
              <>
                <text
                  x={c.x}
                  y={c.y - 4}
                  textAnchor="middle"
                  fill="white"
                  fontSize={Math.min(c.r / 3, 13)}
                  fontWeight={500}
                >
                  {c.name}
                </text>
                <text
                  x={c.x}
                  y={c.y + 10}
                  textAnchor="middle"
                  fill="rgba(255,255,255,0.7)"
                  fontSize={Math.min(c.r / 3.5, 11)}
                >
                  {c.value}
                </text>
              </>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}
```

**Step 4: Run test to verify it passes**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vitest run src/lib/__tests__/bubble-chart.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-next/src/components/viz/bubble-chart.tsx frontend-next/src/lib/__tests__/bubble-chart.test.ts
git commit -m "[ADD] Bubble chart (d3 circle-pack) visualization component"
```

---

## Task 4: Add donut variant to ModuleChart

**Files:**
- Modify: `frontend-next/src/components/viz/module-chart.tsx`

**Step 1: Add `variant` prop to ModuleChart**

In `frontend-next/src/components/viz/module-chart.tsx`, add `variant?: "default" | "donut" | "full-pie"` to the `ModuleChartProps` interface. When `variant="donut"`, set `innerRadius={60} outerRadius={100}`. When `variant="full-pie"`, set `innerRadius={0}`. The existing default behavior already uses `innerRadius={40}` (donut-like), so this is a small tweak.

Modify `ModuleChartProps`:
```typescript
interface ModuleChartProps {
  data: Record<string, unknown>[];
  type?: "bar" | "pie" | "line";
  variant?: "default" | "donut" | "full-pie";
  dataKey?: string;
  nameKey?: string;
  layout?: "vertical" | "horizontal";
  height?: number;
}
```

In the pie chart rendering section, use:
```typescript
innerRadius={variant === "full-pie" ? 0 : variant === "donut" ? 60 : 40}
```

Also add `layout` support: when `layout="horizontal"`, render a horizontal `BarChart` by swapping XAxis/YAxis and adding `layout="vertical"` to BarChart.

Also add `height` prop (default 300) to allow callers to control chart height.

**Step 2: Run existing tests**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vitest run`
Expected: All existing tests pass (no regressions)

**Step 3: Commit**

```bash
git add frontend-next/src/components/viz/module-chart.tsx
git commit -m "[UPT] Add donut/full-pie variants, horizontal layout, and height prop to ModuleChart"
```

---

## Task 5: Create ContributionCalendar component (GitHub)

**Files:**
- Create: `frontend-next/src/components/viz/contribution-calendar.tsx`

**Step 1: Implement the CSS grid heatmap**

File: `frontend-next/src/components/viz/contribution-calendar.tsx`

This component takes raw contribution data (array of `{date, count, level}`) and renders a GitHub-style heatmap using CSS grid. The backend scrapes this data from GitHub and puts it in `graphic[1].cal_actual` as HTML, but we can also parse it. For safety (no dangerouslySetInnerHTML), we render our own grid.

If the backend data is a raw HTML string (legacy), we extract the data attributes from the SVG `rect` elements. If it's already structured data, we use it directly.

```tsx
import { useMemo } from "react";

const LEVEL_COLORS = [
  "bg-zinc-800/50",     // level 0 — no contributions
  "bg-emerald-900/60",  // level 1
  "bg-emerald-700/70",  // level 2
  "bg-emerald-500/80",  // level 3
  "bg-cyan-400",        // level 4
] as const;

interface ContributionDay {
  date: string;
  count: number;
  level: number;
}

interface ContributionCalendarProps {
  htmlData?: string;
  structuredData?: ContributionDay[];
}

/**
 * Parse GitHub contribution calendar HTML to extract day data.
 * Looks for <td> or <rect> elements with data-date, data-count, data-level attributes.
 */
function parseCalendarHtml(html: string): ContributionDay[] {
  const days: ContributionDay[] = [];
  // Match data-date="YYYY-MM-DD" data-level="N" patterns
  const regex =
    /data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"/g;
  let match;
  while ((match = regex.exec(html)) !== null) {
    days.push({
      date: match[1],
      count: 0,
      level: parseInt(match[2], 10),
    });
  }
  return days;
}

export function ContributionCalendar({
  htmlData,
  structuredData,
}: ContributionCalendarProps) {
  const days = useMemo(() => {
    if (structuredData && structuredData.length > 0) return structuredData;
    if (htmlData) return parseCalendarHtml(htmlData);
    return [];
  }, [htmlData, structuredData]);

  if (days.length === 0) {
    return (
      <p className="text-sm italic text-muted-foreground">
        No calendar data available.
      </p>
    );
  }

  // Group by week (columns) — 7 rows (Sun-Sat) x N weeks
  const weeks: ContributionDay[][] = [];
  let currentWeek: ContributionDay[] = [];

  // Pad the first week if it doesn't start on Sunday
  if (days.length > 0) {
    const firstDay = new Date(days[0].date).getDay();
    for (let i = 0; i < firstDay; i++) {
      currentWeek.push({ date: "", count: 0, level: -1 });
    }
  }

  for (const day of days) {
    currentWeek.push(day);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }
  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) {
      currentWeek.push({ date: "", count: 0, level: -1 });
    }
    weeks.push(currentWeek);
  }

  return (
    <div className="overflow-x-auto rounded-md border border-border bg-background/30 p-3">
      <div className="flex gap-[3px]">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-[3px]">
            {week.map((day, di) => (
              <div
                key={`${wi}-${di}`}
                className={`h-[11px] w-[11px] rounded-[2px] ${
                  day.level < 0
                    ? "bg-transparent"
                    : LEVEL_COLORS[day.level] ?? LEVEL_COLORS[0]
                }`}
                title={day.date ? `${day.date}: ${day.count} contributions` : ""}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Run typecheck**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend-next/src/components/viz/contribution-calendar.tsx
git commit -m "[ADD] GitHub contribution calendar heatmap component"
```

---

## Task 6: Create renderer infrastructure and types

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/types.ts`
- Create: `frontend-next/src/components/gatherer/renderers/index.ts`
- Create: `frontend-next/src/components/gatherer/renderers/viz-card.tsx`

**Step 1: Define renderer types and shared VizCard wrapper**

File: `frontend-next/src/components/gatherer/renderers/types.ts`

```typescript
import type { GraphicItem, ModuleResultRaw } from "@/types/api";

/** Props passed to every custom module renderer */
export interface RendererProps {
  result: ModuleResultRaw;
}

/**
 * Safely extract a value from graphic[] at a given index and key.
 * Returns undefined if the path doesn't exist.
 */
export function gfx<T = unknown>(
  graphic: GraphicItem[],
  index: number,
  key: string,
): T | undefined {
  const item = graphic[index];
  if (!item) return undefined;
  return item[key] as T | undefined;
}
```

File: `frontend-next/src/components/gatherer/renderers/viz-card.tsx`

```tsx
import type { ReactNode } from "react";

import { Card } from "@/components/ui/card";

interface VizCardProps {
  title: string;
  children: ReactNode;
  className?: string;
}

/**
 * Wrapper card for individual visualizations within a module renderer.
 * Provides consistent styling with a title header.
 */
export function VizCard({ title, children, className = "" }: VizCardProps) {
  return (
    <Card
      className={`overflow-hidden border-border/60 p-0 ${className}`}
    >
      <div className="border-b border-border/40 px-3 py-2">
        <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {title}
        </h4>
      </div>
      <div className="p-3">{children}</div>
    </Card>
  );
}
```

File: `frontend-next/src/components/gatherer/renderers/index.ts`

```typescript
import type { ComponentType } from "react";

import type { RendererProps } from "./types";

/**
 * Registry of custom module renderers.
 * If a module ID has an entry here, ResultCard renders it instead of the generic view.
 */
export const MODULE_RENDERERS: Record<
  string,
  ComponentType<RendererProps>
> = {
  // Populated by subsequent tasks
};
```

**Step 2: Run typecheck**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend-next/src/components/gatherer/renderers/
git commit -m "[ADD] Module renderer infrastructure: types, VizCard, registry"
```

---

## Task 7: Wire MODULE_RENDERERS into ResultCard

**Files:**
- Modify: `frontend-next/src/components/gatherer/result-card.tsx`

**Step 1: Import and use the renderer registry**

At the top of `result-card.tsx`, add:

```typescript
import { MODULE_RENDERERS } from "@/components/gatherer/renderers";
```

In the `ResultCard` component body, after getting `result` and `mod`, add a check before the existing expanded content:

```tsx
const CustomRenderer = MODULE_RENDERERS[moduleId];
```

In the JSX, replace the expanded body section. If `CustomRenderer` exists, render it directly (always expanded, no tabs). If not, fall back to the existing generic tabs:

```tsx
{expanded && (
  <div className="border-t border-border px-4 py-4">
    {CustomRenderer ? (
      <CustomRenderer result={result} />
    ) : (
      <Tabs defaultValue="details">
        {/* ... existing generic tabs ... */}
      </Tabs>
    )}
  </div>
)}
```

**Step 2: Run existing tests**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vitest run`
Expected: All tests pass (registry is empty so no behavior change)

**Step 3: Commit**

```bash
git add frontend-next/src/components/gatherer/result-card.tsx
git commit -m "[UPT] Wire module renderer registry into ResultCard"
```

---

## Task 8: Create graph data helpers for iKy gather format

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/graph-helpers.ts`
- Test: `frontend-next/src/lib/__tests__/graph-helpers.test.ts`

**Step 1: Write the test**

File: `frontend-next/src/lib/__tests__/graph-helpers.test.ts`

```typescript
import { describe, expect, it } from "vitest";

import { gatherToGraph } from "@/components/gatherer/renderers/graph-helpers";

describe("gatherToGraph", () => {
  it("converts iKy gather array to ForceGraph nodes and links", () => {
    const gather = [
      {
        "name-node": "Github",
        title: "Github",
        subtitle: "",
        icon: "fab fa-github",
        link: "Github",
      },
      {
        "name-node": "GitRepos",
        title: "Repos",
        subtitle: "42",
        icon: "fas fa-folder-open",
        link: "Github",
      },
      {
        "name-node": "GitFollowers",
        title: "Followers",
        subtitle: "120",
        icon: "fas fa-users",
        link: "Github",
      },
    ];
    const { nodes, links } = gatherToGraph(gather);
    expect(nodes).toHaveLength(3);
    expect(nodes[0]).toEqual({
      id: "Github",
      label: "Github",
      group: "primary",
    });
    expect(nodes[1]).toEqual({
      id: "GitRepos",
      label: "Repos: 42",
      group: "Github",
    });
    expect(links).toHaveLength(2);
    expect(links[0]).toEqual({ source: "GitRepos", target: "Github" });
  });

  it("handles picture field as img", () => {
    const gather = [
      {
        "name-node": "Hub",
        title: "Hub",
        subtitle: "",
        link: "Hub",
      },
      {
        "name-node": "Avatar",
        title: "Avatar",
        subtitle: "",
        picture: "https://example.com/avatar.jpg",
        link: "Hub",
      },
    ];
    const { nodes } = gatherToGraph(gather);
    const avatar = nodes.find((n) => n.id === "Avatar");
    expect(avatar?.img).toBe("https://example.com/avatar.jpg");
  });

  it("returns empty for empty input", () => {
    const { nodes, links } = gatherToGraph([]);
    expect(nodes).toEqual([]);
    expect(links).toEqual([]);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vitest run src/lib/__tests__/graph-helpers.test.ts`
Expected: FAIL

**Step 3: Implement graph-helpers**

File: `frontend-next/src/components/gatherer/renderers/graph-helpers.ts`

```typescript
/**
 * Convert iKy backend "gather" array (used by ngx-graphs) to ForceGraph props.
 *
 * The backend gather format is:
 * ```
 * { "name-node": string, title: string, subtitle: string,
 *   icon?: string, link: string, picture?: string, help?: string }
 * ```
 *
 * The `link` field identifies the hub node that this node connects to.
 * Hub nodes have `link === title` (they link to themselves).
 */

interface GatherNode {
  "name-node": string;
  title: string;
  subtitle?: string | number;
  icon?: string;
  link: string;
  picture?: string;
  help?: string;
}

interface GraphNode {
  id: string;
  label: string;
  img?: string;
  group?: string;
}

interface GraphLink {
  source: string;
  target: string;
}

export function gatherToGraph(gather: GatherNode[]): {
  nodes: GraphNode[];
  links: GraphLink[];
} {
  if (!gather || gather.length === 0) return { nodes: [], links: [] };

  const nodes: GraphNode[] = [];
  const links: GraphLink[] = [];

  // First pass: identify hub nodes (link === title)
  const hubIds = new Set<string>();
  for (const item of gather) {
    if (item.link === item.title) {
      hubIds.add(item["name-node"]);
    }
  }

  for (const item of gather) {
    const id = item["name-node"];
    const isHub = hubIds.has(id);
    const subtitle = item.subtitle != null && item.subtitle !== ""
      ? String(item.subtitle)
      : "";
    const label = subtitle ? `${item.title}: ${subtitle}` : item.title;

    nodes.push({
      id,
      label,
      img: item.picture || undefined,
      group: isHub ? "primary" : item.link,
    });

    // Non-hub nodes link to their hub
    if (!isHub) {
      // Find the hub node by title matching the link value
      const hub = gather.find(
        (g) => g.title === item.link && hubIds.has(g["name-node"]),
      );
      if (hub) {
        links.push({ source: id, target: hub["name-node"] });
      }
    }
  }

  return { nodes, links };
}
```

**Step 4: Run test to verify it passes**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vitest run src/lib/__tests__/graph-helpers.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-next/src/components/gatherer/renderers/graph-helpers.ts frontend-next/src/lib/__tests__/graph-helpers.test.ts
git commit -m "[ADD] Graph data helpers for iKy gather format conversion"
```

---

## Task 9: Twitter renderer

This is the most complex renderer (12 visualizations). It serves as the template for all other social profile renderers.

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/twitter-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

**Step 1: Implement the Twitter renderer**

File: `frontend-next/src/components/gatherer/renderers/twitter-renderer.tsx`

```tsx
import { BubbleChart } from "@/components/viz/bubble-chart";
import { ForceGraph } from "@/components/viz/force-graph";
import { ModuleChart } from "@/components/viz/module-chart";
import { TreemapChart } from "@/components/viz/treemap-chart";
import { WordCloud } from "@/components/viz/word-cloud";

import { gatherToGraph } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

export function TwitterRenderer({ result }: RendererProps) {
  const g = result.graphic;

  // graphic[0].social — Force graph (profile info)
  const socialData = gfx<unknown[]>(g, 0, "social");
  const socialGraph = socialData ? gatherToGraph(socialData as never[]) : null;

  // graphic[1].resume.children — Treemap
  const resumeData = gfx<{ children: { name: string; total: number }[] }>(
    g, 1, "resume",
  );

  // graphic[2].popularity — Donut chart
  const popularity = gfx<{ title: string; value: number }[]>(g, 2, "popularity");

  // graphic[3].approval — Donut chart
  const approval = gfx<{ title: string; value: number }[]>(g, 3, "approval");

  // graphic[4].hashtag — Word cloud
  const hashtags = gfx<{ label: string; value: number }[]>(g, 4, "hashtag");

  // graphic[5].users — Force graph (mentioned users)
  const usersData = gfx<unknown[]>(g, 5, "users");
  const usersGraph = usersData ? gatherToGraph(usersData as never[]) : null;

  // graphic[6].tweetslist — Line chart
  const tweetsList = gfx<Record<string, unknown>[]>(g, 6, "tweetslist");

  // graphic[7].week — Bar chart
  const weekData = gfx<{ name: string; value: number }[]>(g, 7, "week");

  // graphic[8].hour — Bar chart
  const hourData = gfx<{ name: string; value: number }[]>(g, 8, "hour");

  // graphic[9].sources — Horizontal bar chart
  const sources = gfx<{ name: string; value: number }[]>(g, 9, "sources");

  // graphic[10].time — Timeline bar chart
  const timeData = gfx<{ name: string; value: number }[]>(g, 10, "time");

  // graphic[11].twvsrt — Pie chart (tweets vs retweets)
  const twvsrt = gfx<{ title: string; value: number }[]>(g, 11, "twvsrt");

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
      {socialGraph && socialGraph.nodes.length >= 2 && (
        <VizCard title="Social Graph" className="md:col-span-2">
          <ForceGraph
            nodes={socialGraph.nodes}
            links={socialGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {resumeData?.children && resumeData.children.length > 0 && (
        <VizCard title="Resume">
          <TreemapChart data={resumeData.children} />
        </VizCard>
      )}

      {popularity && popularity.length > 0 && (
        <VizCard title="Popularity">
          <ModuleChart
            data={popularity.map((d) => ({ name: d.title, value: d.value }))}
            type="pie"
            variant="donut"
            height={250}
          />
        </VizCard>
      )}

      {approval && approval.length > 0 && (
        <VizCard title="Approval">
          <ModuleChart
            data={approval.map((d) => ({ name: d.title, value: d.value }))}
            type="pie"
            variant="donut"
            height={250}
          />
        </VizCard>
      )}

      {hashtags && hashtags.length > 0 && (
        <VizCard title="Hashtags">
          <WordCloud
            words={hashtags.map((h) => ({ text: h.label, value: h.value }))}
          />
        </VizCard>
      )}

      {usersGraph && usersGraph.nodes.length >= 2 && (
        <VizCard title="Mentioned Users">
          <ForceGraph
            nodes={usersGraph.nodes}
            links={usersGraph.links}
            height={300}
          />
        </VizCard>
      )}

      {tweetsList && tweetsList.length > 0 && (
        <VizCard title="Tweets" className="md:col-span-2">
          <ModuleChart data={tweetsList} type="line" height={250} />
        </VizCard>
      )}

      {weekData && weekData.length > 0 && (
        <VizCard title="Activity by Day">
          <ModuleChart data={weekData} type="bar" height={200} />
        </VizCard>
      )}

      {hourData && hourData.length > 0 && (
        <VizCard title="Activity by Hour">
          <ModuleChart data={hourData} type="bar" height={200} />
        </VizCard>
      )}

      {sources && sources.length > 0 && (
        <VizCard title="Sources">
          <ModuleChart data={sources} type="bar" layout="horizontal" height={200} />
        </VizCard>
      )}

      {timeData && timeData.length > 0 && (
        <VizCard title="Timeline">
          <ModuleChart data={timeData} type="bar" height={200} />
        </VizCard>
      )}

      {twvsrt && twvsrt.length > 0 && (
        <VizCard title="Tweets vs Retweets">
          <ModuleChart
            data={twvsrt.map((d) => ({ name: d.title, value: d.value }))}
            type="pie"
            variant="full-pie"
            height={250}
          />
        </VizCard>
      )}
    </div>
  );
}
```

**Step 2: Register in index.ts**

Add to `frontend-next/src/components/gatherer/renderers/index.ts`:
```typescript
import { TwitterRenderer } from "./twitter-renderer";

export const MODULE_RENDERERS: Record<string, ComponentType<RendererProps>> = {
  twitter: TwitterRenderer,
};
```

**Step 3: Typecheck**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx tsc --noEmit`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend-next/src/components/gatherer/renderers/twitter-renderer.tsx frontend-next/src/components/gatherer/renderers/index.ts
git commit -m "[ADD] Twitter module renderer with 12 visualizations"
```

---

## Task 10: Instagram renderer

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/instagram-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

Same pattern as Twitter. Instagram visualizations:
- `graphic[0].instagram` — Force graph
- `graphic[1].popularig` — Line chart (likes/comments per post)
- `graphic[2].mediatype` — Donut chart
- `graphic[3].hashtag` — Word cloud
- `graphic[4].mention` — Word cloud
- `graphic[5].tagged` — Word cloud
- `graphic[6].hour` — Bar chart
- `graphic[7].week` — Bar chart
- `graphic[8].photos` — Force graph (images as picture nodes)
- `graphic[9].list` — DataTable (posts)
- `graphic[10].location` — LocationMap

Register as `instagram: InstagramRenderer` in index.ts.

**Commit:** `[ADD] Instagram module renderer with 11 visualizations`

---

## Task 11: TikTok renderer

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/tiktok-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

TikTok visualizations:
- `graphic[0].tiktok` — Force graph
- `graphic[1].resume.children` — Treemap
- `graphic[2].posts` — Line chart
- `graphic[3].hashtag` — Word cloud
- `graphic[4].hour` — Bar chart
- `graphic[5].week` — Bar chart
- `graphic[6].videos` — Force graph (thumbnails)
- `graphic[7].time` — Bar chart (timeline)

Register as `tiktok: TiktokRenderer` in index.ts.

**Commit:** `[ADD] TikTok module renderer with 8 visualizations`

---

## Task 12: Twitch renderer

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/twitch-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

Twitch visualizations:
- `graphic[0].twitch` — Force graph
- `graphic[1].duration` — Horizontal bar chart
- `graphic[2].hour` — Bar chart
- `graphic[3].week` — Bar chart
- `graphic[4].list` — DataTable (videos)
- `graphic[5].time` — Bar chart (timeline)

Register as `twitch: TwitchRenderer` in index.ts.

**Commit:** `[ADD] Twitch module renderer with 6 visualizations`

---

## Task 13: Reddit renderer

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/reddit-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

Reddit visualizations:
- `graphic[0].reddit` — Force graph
- `graphic[1].bubble` — BubbleChart (subreddit topics)
- `graphic[2].hour` — Bar chart
- `graphic[3].week` — Bar chart

Register as `reddit: RedditRenderer` in index.ts.

**Commit:** `[ADD] Reddit module renderer with 4 visualizations`

---

## Task 14: Spotify renderer

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/spotify-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

Spotify visualizations:
- `graphic[0].spotify` — Force graph
- `graphic[1].playlists` — Horizontal bar chart
- `graphic[2].lang` — BubbleChart (music languages)
- `graphic[3].autors` — Word cloud (artists)
- `graphic[4].words` — Word cloud (track words)

Register as `spotify: SpotifyRenderer` in index.ts.

**Commit:** `[ADD] Spotify module renderer with 5 visualizations`

---

## Task 15: LinkedIn renderer

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/linkedin-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

LinkedIn visualizations:
- `graphic[0].linkedin` — Force graph
- `graphic[1].skill` — BubbleChart (skills by endorsement)
- `graphic[2].pos` — DataTable (job positions)
- `graphic[3].certs` — DataTable (certifications)

Register as `linkedin: LinkedinRenderer` in index.ts.

**Commit:** `[ADD] LinkedIn module renderer with 4 visualizations`

---

## Task 16: Mastodon, Keybase, Venmo renderers

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/mastodon-renderer.tsx`
- Create: `frontend-next/src/components/gatherer/renderers/keybase-renderer.tsx`
- Create: `frontend-next/src/components/gatherer/renderers/venmo-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

**Mastodon:**
- `graphic[0].mastodon` — Force graph
- `graphic[1].list` — DataTable (accounts)
- `graphic[2].social` — Force graph

**Keybase:**
- `graphic[0].keybase` — Force graph
- `graphic[1].devices` — Force graph
- `graphic[2].social` — Force graph

**Venmo:**
- `graphic[0].venmo` — Force graph
- `graphic[1].friends` — Force graph
- `graphic[2].trans` — DataTable (transactions)

Register all three in index.ts.

**Commit:** `[ADD] Mastodon, Keybase, Venmo module renderers`

---

## Task 17: GitHub renderer

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/github-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

GitHub visualizations:
- `graphic[0].github` — Force graph (profile info)
- `graphic[1].cal_actual` — ContributionCalendar heatmap

```tsx
import { ContributionCalendar } from "@/components/viz/contribution-calendar";
import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

export function GithubRenderer({ result }: RendererProps) {
  const g = result.graphic;

  const githubData = gfx<unknown[]>(g, 0, "github");
  const graph = githubData ? gatherToGraph(githubData as never[]) : null;

  // cal_actual is a raw HTML string from the backend
  const calHtml = gfx<string>(g, 1, "cal_actual");

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {graph && graph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-1">
          <ForceGraph
            nodes={graph.nodes}
            links={graph.links}
            height={350}
          />
        </VizCard>
      )}

      {calHtml && (
        <VizCard title="Contributions" className="md:col-span-2">
          <ContributionCalendar htmlData={calHtml} />
        </VizCard>
      )}
    </div>
  );
}
```

Register as `github: GithubRenderer` in index.ts.

**Commit:** `[ADD] GitHub module renderer with force graph and contribution calendar`

---

## Task 18: Account check renderers (Holehe, Sherlock, Socialscan)

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/account-check-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

These share the same pattern: force graph (found sites) + scrollable list (all sites with status).

```tsx
import { ForceGraph } from "@/components/viz/force-graph";
import { DataTable } from "@/components/viz/data-table";

import { gatherToGraph } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Shared renderer for account-existence-checking modules.
 * Supports: holehe, sherlock, socialscan
 */
function AccountCheckLayout({
  graphData,
  listData,
  graphTitle,
  listTitle,
}: {
  graphData: unknown[] | undefined;
  listData: Record<string, unknown>[] | undefined;
  graphTitle: string;
  listTitle: string;
}) {
  const graph = graphData ? gatherToGraph(graphData as never[]) : null;

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {graph && graph.nodes.length >= 2 && (
        <VizCard title={graphTitle} className="md:col-span-2">
          <ForceGraph
            nodes={graph.nodes}
            links={graph.links}
            height={350}
          />
        </VizCard>
      )}

      {listData && listData.length > 0 && (
        <VizCard title={listTitle} className="md:col-span-1">
          <DataTable data={listData} searchable pageSize={15} />
        </VizCard>
      )}
    </div>
  );
}

export function HoleheRenderer({ result }: RendererProps) {
  return (
    <AccountCheckLayout
      graphData={gfx<unknown[]>(result.graphic, 0, "holehe")}
      listData={gfx<Record<string, unknown>[]>(result.graphic, 1, "lists")}
      graphTitle="Found Accounts"
      listTitle="All Sites Checked"
    />
  );
}

export function SherlockRenderer({ result }: RendererProps) {
  return (
    <AccountCheckLayout
      graphData={gfx<unknown[]>(result.graphic, 0, "sherlock")}
      listData={gfx<Record<string, unknown>[]>(result.graphic, 1, "lists")}
      graphTitle="Claimed Accounts"
      listTitle="All Sites Checked"
    />
  );
}

export function SocialscanRenderer({ result }: RendererProps) {
  const emailGraph = gfx<unknown[]>(result.graphic, 0, "social_email");
  const userGraph = gfx<unknown[]>(result.graphic, 1, "social_user");
  const emailNodes = emailGraph ? gatherToGraph(emailGraph as never[]) : null;
  const userNodes = userGraph ? gatherToGraph(userGraph as never[]) : null;

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      {emailNodes && emailNodes.nodes.length >= 2 && (
        <VizCard title="Email Registrations">
          <ForceGraph
            nodes={emailNodes.nodes}
            links={emailNodes.links}
            height={300}
          />
        </VizCard>
      )}
      {userNodes && userNodes.nodes.length >= 2 && (
        <VizCard title="Username Registrations">
          <ForceGraph
            nodes={userNodes.nodes}
            links={userNodes.links}
            height={300}
          />
        </VizCard>
      )}
    </div>
  );
}
```

Register `holehe: HoleheRenderer`, `sherlock: SherlockRenderer`, `socialscan: SocialscanRenderer` in index.ts.

**Commit:** `[ADD] Account check renderers for Holehe, Sherlock, Socialscan`

---

## Task 19: Search and Dorks renderers

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/search-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

Both Search and Dorks share the same structure:
- `graphic[0].names` — Word cloud
- `graphic[1].username` — Word cloud
- `graphic[2].social` — Force graph
- `graphic[3].rawresults` — DataTable (all results)
- `graphic[4].searches` — DataTable (filtered results)
- `graphic[5].mentions` — Word cloud
- `graphic[6].hashtags` — Word cloud
- `graphic[7].emails` — Word cloud

Create a single `SearchResultRenderer` component used by both module IDs.

The list items from the backend have shape: `{ title, simple, url, desc, icon, link }`. The DataTable should display `simple` (title), `desc` (description), and `url` (as a clickable link). Create custom column definitions for the DataTable.

Register `search: SearchResultRenderer`, `dorks: SearchResultRenderer` in index.ts.

**Commit:** `[ADD] Search and Dorks module renderers with word clouds and result lists`

---

## Task 20: Leak renderers (leaks, leaklookup, darkpass, psbdmp)

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/leak-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

**Leak/HIBP:** `graphic[0].leak` — Force graph (breached databases)

**LeakLookup:** `graphic[0].leaklookup` — Accordion-style list. Each item is a breach site with nested field/value pairs. Render as expandable sections using shadcn Collapsible or nested card.

**Darkpass:** `graphic[0].darkpass` — Simple list of leaked passwords.

**PsbDmp:**
- `graphic[0].psbdmp` — Word cloud (paste content words)
- `graphic[1].list` — DataTable (paste entries)

Register `leaks: LeakGraphRenderer`, `leaklookup: LeakLookupRenderer`, `darkpass: DarkpassRenderer`, `psbdmp: PsbdmpRenderer` in index.ts.

**Commit:** `[ADD] Leak module renderers for HIBP, LeakLookup, Darkpass, PsbDmp`

---

## Task 21: Enrichment renderers (EmailRep, FullContact, PeopleDataLabs)

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/enrichment-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

**EmailRep:**
- `graphic[0].emailrep` — Force graph (reputation details)
- `graphic[1].social` — Force graph (social profiles)

**FullContact:**
- `graphic[0].fullcontact` — Force graph (enriched profile)
- `graphic[1].cloud` — Word cloud (digital footprint)

**PeopleDataLabs:**
- `graphic[0].peopledatalabs` — Force graph (enriched profile)
- `graphic[1].social` — Force graph (social profiles)

Register `emailrep: EmailRepRenderer`, `fullcontact: FullContactRenderer`, `peopledatalabs: PeopleDataLabsRenderer` in index.ts.

**Commit:** `[ADD] Enrichment module renderers for EmailRep, FullContact, PeopleDataLabs`

---

## Task 22: Simple graph renderers (GitLab, Tinder, Skype, GhostProject)

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/simple-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

These modules only have a single force graph visualization. Create a generic `SimpleGraphRenderer` factory:

```typescript
function makeSimpleRenderer(graphKey: string, title: string) {
  return function SimpleRenderer({ result }: RendererProps) {
    const data = gfx<unknown[]>(result.graphic, 0, graphKey);
    const graph = data ? gatherToGraph(data as never[]) : null;
    if (!graph || graph.nodes.length < 2) return null;
    return (
      <VizCard title={title}>
        <ForceGraph nodes={graph.nodes} links={graph.links} height={350} />
      </VizCard>
    );
  };
}
```

Register:
- `gitlab: makeSimpleRenderer("gitlab", "GitLab Profile")`
- `tinder: makeSimpleRenderer("tinder", "Tinder Profile")`
- `ghostproject: makeSimpleRenderer("ghostproject", "GhostProject")`
- `skype` gets a simple status text renderer (no graph)

**Commit:** `[ADD] Simple graph renderers for GitLab, Tinder, Skype, GhostProject`

---

## Task 23: Tweetiment renderer

**Files:**
- Create: `frontend-next/src/components/gatherer/renderers/tweetiment-renderer.tsx`
- Modify: `frontend-next/src/components/gatherer/renderers/index.ts`

**Tweetiment:** `graphic[0].sentiment` — Multi-series line chart (positive/negative/neutral)

Register as `tweetiment: TweetimentRenderer` in index.ts.

**Commit:** `[ADD] Tweetiment sentiment analysis renderer`

---

## Task 24: Update MSW mock data for module-specific formats

**Files:**
- Modify: `frontend-next/src/mocks/data.ts`
- Modify: `frontend-next/src/mocks/handlers.ts`

Update the mock data to use the real iKy backend data format (positional `graphic[]` arrays with module-specific keys). Add mock data for at least: twitter, github, holehe, search — these cover the main renderer patterns.

Update handlers.ts to return the correct mock data based on the module name in the dispatch request.

**Commit:** `[UPT] Update MSW mocks with module-specific graphic data formats`

---

## Task 25: Final integration test and cleanup

**Step 1: Run all unit tests**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vitest run`
Expected: All tests pass

**Step 2: Run typecheck**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx tsc --noEmit`
Expected: No errors

**Step 3: Run build**

Run: `cd /home/jpdborgna/src/iKy/frontend-next && npx vite build`
Expected: Build succeeds with no errors

**Step 4: Verify all renderers are registered**

Check that `MODULE_RENDERERS` in `index.ts` has entries for all 28 modules (or all modules that have custom visualizations — some may still use generic fallback if they have no dedicated Angular component, like `usersearch`).

Expected module count in registry: ~25 custom renderers (twitter, instagram, tiktok, twitch, reddit, spotify, linkedin, mastodon, keybase, venmo, github, holehe, sherlock, socialscan, search, dorks, leaks, leaklookup, darkpass, psbdmp, emailrep, fullcontact, peopledatalabs, gitlab, tinder, skype, ghostproject, tweetiment).

**Step 5: Commit any final cleanups**

```bash
git commit -m "[UPT] Final integration cleanup for module renderers"
```

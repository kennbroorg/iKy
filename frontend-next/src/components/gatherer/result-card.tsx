import { useState } from "react";

import { ChevronDown, ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";
import { ModuleChart } from "@/components/viz/module-chart";
import { getModuleIcon } from "@/lib/icon-map";
import { getModule } from "@/lib/module-registry";
import type { TaskEntry } from "@/stores/gather-store";
import type { GraphicItem } from "@/types/api";
import type { ModuleConfig } from "@/types/modules";

interface ResultCardProps {
  moduleId: string;
  task: TaskEntry;
}

const VALIDATION_STYLES: Record<
  string,
  { label: string; className: string } | null
> = {
  hard: {
    label: "Hard",
    className: "bg-emerald-600/20 text-emerald-400 border-emerald-500/30",
  },
  soft: {
    label: "Soft",
    className: "bg-yellow-600/20 text-yellow-400 border-yellow-500/30",
  },
  no: {
    label: "No",
    className: "bg-zinc-600/20 text-zinc-400 border-zinc-500/30",
  },
  not_used: null,
};

// ---------------------------------------------------------------------------
// Graph data extraction helpers
// ---------------------------------------------------------------------------

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

/**
 * Parse graphic items to extract nodes and links for a force-directed graph.
 * Looks for typical iKy graph structures: nodes with id/label, edges with
 * source/target, or nested "social"/"details" arrays that can be mapped.
 */
function extractGraphData(graphic: GraphicItem[]): {
  nodes: GraphNode[];
  links: GraphLink[];
} | null {
  const nodes: GraphNode[] = [];
  const links: GraphLink[] = [];
  const seenNodeIds = new Set<string>();

  for (const item of graphic) {
    // Look for explicit graph structures
    if (Array.isArray(item.nodes) && Array.isArray(item.links)) {
      for (const n of item.nodes as Record<string, unknown>[]) {
        const id = String(n.id ?? n.name ?? "");
        if (id && !seenNodeIds.has(id)) {
          seenNodeIds.add(id);
          nodes.push({
            id,
            label: String(n.label ?? n.name ?? id),
            img: n.img ? String(n.img) : undefined,
            group: n.group ? String(n.group) : undefined,
          });
        }
      }
      for (const l of item.links as Record<string, unknown>[]) {
        links.push({
          source: String(l.source ?? ""),
          target: String(l.target ?? ""),
        });
      }
      continue;
    }

    // Look for social array -> build graph from social connections
    if (Array.isArray(item.social) && item.social.length > 0) {
      // Create a central node from the module data
      const centerId = String(item.name ?? item.username ?? "center");
      if (!seenNodeIds.has(centerId)) {
        seenNodeIds.add(centerId);
        nodes.push({
          id: centerId,
          label: centerId,
          group: "primary",
        });
      }

      for (const social of item.social as Record<string, unknown>[]) {
        const name = String(social.name ?? social.source ?? social.url ?? "");
        if (name && !seenNodeIds.has(name)) {
          seenNodeIds.add(name);
          nodes.push({
            id: name,
            label: name,
            group: String(social.source ?? "social"),
          });
          links.push({ source: centerId, target: name });
        }
      }
    }

    // Build graph from any remaining key-value pairs that look like connections
    for (const [key, value] of Object.entries(item)) {
      if (
        key === "details" ||
        key === "social" ||
        key === "nodes" ||
        key === "links"
      )
        continue;

      if (
        Array.isArray(value) &&
        value.length > 0 &&
        typeof value[0] === "object" &&
        value[0] !== null
      ) {
        // Array of objects -> each could be a node
        const groupName = key;
        const centerId = `__${key}_center`;
        if (!seenNodeIds.has(centerId)) {
          seenNodeIds.add(centerId);
          nodes.push({
            id: centerId,
            label: key.replace(/_/g, " "),
            group: "primary",
          });
        }

        for (const entry of value as Record<string, unknown>[]) {
          const name = String(
            entry.name ?? entry.title ?? entry.label ?? entry.id ?? "",
          );
          if (name && !seenNodeIds.has(name)) {
            seenNodeIds.add(name);
            nodes.push({ id: name, label: name, group: groupName });
            links.push({ source: centerId, target: name });
          }
        }
      }
    }
  }

  if (nodes.length < 2) return null;
  return { nodes, links };
}

// ---------------------------------------------------------------------------
// Chart data extraction helpers
// ---------------------------------------------------------------------------

/**
 * Extract chart-friendly data from graphic items.
 * Looks for key-value pairs with numeric values, or arrays with
 * objects that have a name + value structure.
 */
function extractChartData(
  graphic: GraphicItem[],
): Record<string, unknown>[] | null {
  const chartData: Record<string, unknown>[] = [];

  for (const item of graphic) {
    for (const [key, value] of Object.entries(item)) {
      if (key === "details" || key === "social") continue;

      // If value is a number, add as a chart entry
      if (typeof value === "number" || (typeof value === "string" && !isNaN(Number(value)) && value.trim() !== "")) {
        chartData.push({ name: key.replace(/_/g, " "), value: Number(value) });
      }

      // If value is an array of objects with name+value, use directly
      if (Array.isArray(value) && value.length > 0) {
        const first = value[0];
        if (typeof first === "object" && first !== null) {
          const obj = first as Record<string, unknown>;
          // Check if objects have a value-like field
          const hasValue = Object.values(obj).some(
            (v) => typeof v === "number",
          );
          if (hasValue) {
            for (const entry of value as Record<string, unknown>[]) {
              chartData.push(entry);
            }
            // If we found array chart data, use it directly
            if (chartData.length > 0) return chartData;
          }
        }
      }
    }
  }

  // Filter out entries without numeric values
  const filtered = chartData.filter((d) =>
    Object.values(d).some((v) => typeof v === "number"),
  );

  return filtered.length >= 2 ? filtered : null;
}

// ---------------------------------------------------------------------------
// Table data extraction
// ---------------------------------------------------------------------------

/**
 * Extract tabular data from graphic items.
 * Returns arrays of objects suitable for DataTable.
 */
function extractTableData(
  graphic: GraphicItem[],
): Array<{ label: string; rows: Record<string, unknown>[] }> {
  const result: Array<{ label: string; rows: Record<string, unknown>[] }> = [];

  for (const item of graphic) {
    for (const [key, value] of Object.entries(item)) {
      if (!Array.isArray(value) || value.length === 0) continue;

      const firstRow = value[0];
      if (
        typeof firstRow === "object" &&
        firstRow !== null &&
        !Array.isArray(firstRow)
      ) {
        result.push({
          label: key,
          rows: value as Record<string, unknown>[],
        });
      } else if (typeof firstRow === "string" || typeof firstRow === "number") {
        // Convert primitive arrays to objects with a single column
        result.push({
          label: key,
          rows: value.map((v) => ({ [key]: v })),
        });
      }
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// View components
// ---------------------------------------------------------------------------

function KeyValueView({ graphic }: { graphic: GraphicItem[] }) {
  // Extract key-value pairs from graphic items
  const entries: Array<{ key: string; value: unknown }> = [];

  for (const item of graphic) {
    for (const [key, value] of Object.entries(item)) {
      if (key === "details" || key === "social") continue;
      entries.push({ key, value });
    }
  }

  // Show detail arrays if present
  const detailArrays = graphic
    .flatMap((g) => (Array.isArray(g.details) ? g.details : []))
    .filter(Boolean);

  if (entries.length === 0 && detailArrays.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">No data available.</p>
    );
  }

  return (
    <div className="space-y-3">
      {entries.length > 0 && (
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
          {entries.map(({ key, value }, i) => (
            <div key={i} className="contents">
              <dt className="font-medium text-muted-foreground capitalize">
                {key.replace(/_/g, " ")}
              </dt>
              <dd className="text-foreground truncate">
                {typeof value === "object"
                  ? JSON.stringify(value)
                  : String(value ?? "")}
              </dd>
            </div>
          ))}
        </dl>
      )}

      {detailArrays.length > 0 && (
        <div className="space-y-1.5">
          <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Details
          </h4>
          <ul className="space-y-1">
            {detailArrays.map((item, i) => (
              <li
                key={i}
                className="rounded-md border border-border bg-background/50 px-3 py-1.5 text-sm"
              >
                {typeof item === "object"
                  ? JSON.stringify(item)
                  : String(item)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function DetailsView({
  graphic,
  mod,
}: {
  graphic: GraphicItem[];
  mod: ModuleConfig;
}) {
  if (!graphic || graphic.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">No data available.</p>
    );
  }

  const viz = mod.visualization;
  const sections: React.ReactNode[] = [];

  // Render force graph if configured
  if (viz.useGenericGraph) {
    const graphData = extractGraphData(graphic);
    if (graphData && graphData.nodes.length >= 2) {
      sections.push(
        <div key="graph" className="space-y-2">
          <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Relationship Graph
          </h4>
          <ForceGraph
            nodes={graphData.nodes}
            links={graphData.links}
            height={350}
          />
        </div>,
      );
    }
  }

  // Render chart if configured
  if (viz.useGenericChart) {
    const chartData = extractChartData(graphic);
    if (chartData && chartData.length >= 2) {
      sections.push(
        <div key="chart" className="space-y-2">
          <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Chart
          </h4>
          <ModuleChart data={chartData} />
        </div>,
      );
    }
  }

  // Always show key-value pairs as well
  sections.push(<KeyValueView key="kv" graphic={graphic} />);

  return <div className="space-y-4">{sections}</div>;
}

function TableView({ graphic }: { graphic: GraphicItem[] }) {
  const tableGroups = extractTableData(graphic);

  if (tableGroups.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No tabular data available.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {tableGroups.map(({ label, rows }) => (
        <div key={label} className="space-y-2">
          <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label.replace(/_/g, " ")}
          </h4>
          <DataTable data={rows} searchable={rows.length > 5} pageSize={10} />
        </div>
      ))}
    </div>
  );
}

function RawView({ raw }: { raw: Record<string, unknown> | unknown[] }) {
  return (
    <pre className="max-h-96 overflow-auto rounded-md border border-border bg-background/80 p-4 font-mono text-xs leading-relaxed text-foreground/80">
      {JSON.stringify(raw, null, 2)}
    </pre>
  );
}

export function ResultCard({ moduleId, task }: ResultCardProps) {
  const [expanded, setExpanded] = useState(false);
  const mod = getModule(moduleId);
  const result = task.result;

  if (!mod || !result) return null;

  const Icon = getModuleIcon(mod.icon);
  const validation = VALIDATION_STYLES[result.validation];

  return (
    <Card className="overflow-hidden border-border/60 py-0 gap-0">
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/20"
      >
        <Icon className="size-5 shrink-0 text-primary" />
        <span className="font-medium text-sm">{mod.label}</span>
        {validation && (
          <Badge className={validation.className}>{validation.label}</Badge>
        )}
        <div className="ml-auto">
          {expanded ? (
            <ChevronDown className="size-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="size-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Body */}
      {expanded && (
        <div className="border-t border-border px-4 py-4">
          <Tabs defaultValue="details">
            <TabsList className="bg-muted/50 border border-border mb-4">
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="table">Table</TabsTrigger>
              <TabsTrigger value="raw">Raw</TabsTrigger>
            </TabsList>
            <TabsContent value="details">
              <DetailsView graphic={result.graphic} mod={mod} />
            </TabsContent>
            <TabsContent value="table">
              <TableView graphic={result.graphic} />
            </TabsContent>
            <TabsContent value="raw">
              <RawView raw={result.raw} />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </Card>
  );
}

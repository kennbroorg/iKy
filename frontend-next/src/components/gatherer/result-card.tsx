import { useState } from "react";

import { ChevronDown, ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getModuleIcon } from "@/lib/icon-map";
import { getModule } from "@/lib/module-registry";
import type { TaskEntry } from "@/stores/gather-store";
import type { GraphicItem } from "@/types/api";

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

function DetailsView({ graphic }: { graphic: GraphicItem[] }) {
  if (!graphic || graphic.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">No data available.</p>
    );
  }

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

function TableView({ graphic }: { graphic: GraphicItem[] }) {
  // Find any array data within graphic items
  const arrayData: Array<{ label: string; rows: unknown[] }> = [];

  for (const item of graphic) {
    for (const [key, value] of Object.entries(item)) {
      if (Array.isArray(value) && value.length > 0) {
        arrayData.push({ label: key, rows: value });
      }
    }
  }

  if (arrayData.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No tabular data available.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {arrayData.map(({ label, rows }) => {
        // Extract column headers from first row if it's an object
        const firstRow = rows[0];
        const isObjRows =
          typeof firstRow === "object" && firstRow !== null && !Array.isArray(firstRow);
        const columns = isObjRows ? Object.keys(firstRow as Record<string, unknown>) : [];

        return (
          <div key={label} className="space-y-2">
            <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {label.replace(/_/g, " ")}
            </h4>
            <div className="overflow-auto rounded-md border border-border">
              <table className="w-full text-sm">
                {isObjRows && columns.length > 0 && (
                  <thead>
                    <tr className="border-b border-border bg-muted/50">
                      {columns.map((col) => (
                        <th
                          key={col}
                          className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground"
                        >
                          {col.replace(/_/g, " ")}
                        </th>
                      ))}
                    </tr>
                  </thead>
                )}
                <tbody>
                  {rows.map((row, i) => (
                    <tr
                      key={i}
                      className="border-b border-border/50 last:border-0 hover:bg-muted/20"
                    >
                      {isObjRows ? (
                        columns.map((col) => (
                          <td key={col} className="px-3 py-1.5 text-foreground">
                            {String(
                              (row as Record<string, unknown>)[col] ?? "",
                            )}
                          </td>
                        ))
                      ) : (
                        <td className="px-3 py-1.5 text-foreground">
                          {typeof row === "object"
                            ? JSON.stringify(row)
                            : String(row)}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
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
              <DetailsView graphic={result.graphic} />
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

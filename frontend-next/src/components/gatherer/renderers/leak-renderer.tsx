import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";
import { WordCloud } from "@/components/viz/word-cloud";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Leak/HIBP (leaks) module.
 *
 * Backend `graphic.append()`:
 *  0 {"leaks": gather}  — gather format — Force graph (breached databases)
 */
export function LeakGraphRenderer({ result }: RendererProps) {
  const { graphic } = result;

  const leakData = gfx<GatherItem[]>(graphic, 0, "leaks");
  const leakGraph = leakData ? gatherToGraph(leakData) : null;

  return (
    <div className="grid grid-cols-1 gap-4">
      {leakGraph && leakGraph.nodes.length >= 2 && (
        <VizCard title="Breached Databases">
          <ForceGraph
            nodes={leakGraph.nodes}
            links={leakGraph.links}
            height={400}
          />
        </VizCard>
      )}
    </div>
  );
}

/**
 * Renderer for the LeakLookup module.
 *
 * Backend `graphic.append()`:
 *  0 {"email": leak_email}  — Array of {name: string, value: {name,value}[]}
 *    Each entry is a leak source with nested field/value pairs.
 *
 * Flattens the nested structure into a DataTable grouped by source.
 */
export function LeakLookupRenderer({ result }: RendererProps) {
  const { graphic } = result;

  const rawData = gfx<{ name: string; value: { name: string; value: string }[] }[]>(
    graphic,
    0,
    "email",
  );

  // Flatten nested name/value into flat rows for the DataTable
  const tableRows: Record<string, unknown>[] = [];
  if (rawData) {
    for (const entry of rawData) {
      if (Array.isArray(entry.value)) {
        for (const detail of entry.value) {
          tableRows.push({
            source: entry.name,
            field: detail.name,
            value: String(detail.value ?? ""),
          });
        }
      } else {
        // Fallback: show source with raw data
        tableRows.push({
          source: entry.name,
          field: "data",
          value: String(entry.value ?? ""),
        });
      }
    }
  }

  return (
    <div className="grid grid-cols-1 gap-4">
      {tableRows.length > 0 && (
        <VizCard title="Leak Lookup Results">
          <DataTable data={tableRows} searchable pageSize={15} />
        </VizCard>
      )}
    </div>
  );
}

/**
 * Renderer for the Darkpass module.
 *
 * Backend `graphic.append()`:
 *  0 {"darkpass": gather}  — Array of {username, password} entries
 */
export function DarkpassRenderer({ result }: RendererProps) {
  const { graphic } = result;

  const darkpassData = gfx<Record<string, unknown>[]>(
    graphic,
    0,
    "darkpass",
  );

  return (
    <div className="grid grid-cols-1 gap-4">
      {darkpassData && darkpassData.length > 0 && (
        <VizCard title="Leaked Passwords">
          <DataTable data={darkpassData} searchable pageSize={10} />
        </VizCard>
      )}
    </div>
  );
}

/**
 * Renderer for the PsbDmp module.
 *
 * Backend `graphic.append()`:
 *  0 {"dlist": dump_list}  — Array of {id, tags, time} — paste entries
 *  1 {"dword": dump_word}  — Array of {label, value} — word frequencies
 */
export function PsbdmpRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Paste entries table
  const listData = gfx<Record<string, unknown>[]>(graphic, 0, "dlist");

  // 1 — Paste content word cloud
  const cloudData = gfx<{ label: string; value: number }[]>(
    graphic,
    1,
    "dword",
  );
  const cloudWords = cloudData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {cloudWords && cloudWords.length > 0 && (
        <VizCard title="Paste Content">
          <WordCloud words={cloudWords} />
        </VizCard>
      )}

      {listData && listData.length > 0 && (
        <VizCard title="Paste Entries">
          <DataTable data={listData} searchable pageSize={10} />
        </VizCard>
      )}
    </div>
  );
}

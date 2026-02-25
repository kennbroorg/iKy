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
 * Reads 1 visualization from `result.graphic[0]`:
 *  0 leak — gather format — Force graph (breached databases)
 */
export function LeakGraphRenderer({ result }: RendererProps) {
  const { graphic } = result;

  const leakData = gfx<GatherItem[]>(graphic, 0, "leak");
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
 * Reads 1 visualization from `result.graphic[0]`:
 *  0 leaklookup — Array of {source, data} entries where data holds leaked fields.
 *
 * Flattens the nested structure into a DataTable grouped by source.
 */
export function LeakLookupRenderer({ result }: RendererProps) {
  const { graphic } = result;

  const rawData = gfx<{ source: string; data: Record<string, string> }[]>(
    graphic,
    0,
    "leaklookup",
  );

  // Flatten nested source/data into flat rows for the DataTable
  const tableRows: Record<string, unknown>[] = [];
  if (rawData) {
    for (const entry of rawData) {
      if (entry.data && typeof entry.data === "object") {
        for (const [field, value] of Object.entries(entry.data)) {
          tableRows.push({
            source: entry.source,
            field,
            value: String(value),
          });
        }
      } else {
        // If data is not a nested object, show source with raw data
        tableRows.push({
          source: entry.source,
          field: "data",
          value: String(entry.data ?? ""),
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
 * Reads 1 visualization from `result.graphic[0]`:
 *  0 darkpass — Array of {password?, status?} entries — leaked passwords
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
 * Reads 2 visualizations from `result.graphic[0..1]`:
 *  0 psbdmp — Word cloud (paste content word frequencies)
 *  1 list   — DataTable (paste entries with time, id, tags)
 */
export function PsbdmpRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Paste content word cloud
  const cloudData = gfx<{ label: string; value: number }[]>(
    graphic,
    0,
    "psbdmp",
  );
  const cloudWords = cloudData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  // 1 — Paste entries table
  const listData = gfx<Record<string, unknown>[]>(graphic, 1, "list");

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

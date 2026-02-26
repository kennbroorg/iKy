import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Venmo module.
 *
 * Reads 1 visualization from `result.graphic[0]`:
 *  0 user — Force graph (profile info, gather format)
 *
 * NOTE: The backend comments out `friends` (index 1) and `trans` (index 2),
 * so they are never present in the response.
 */
export function VenmoRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Venmo profile force graph (key: "user")
  const venmoData = gfx<GatherItem[]>(graphic, 0, "user");
  const venmoGraph = venmoData ? gatherToGraph(venmoData) : null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Venmo profile graph — spans 2 cols */}
      {venmoGraph && venmoGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={venmoGraph.nodes}
            links={venmoGraph.links}
            height={350}
          />
        </VizCard>
      )}
    </div>
  );
}

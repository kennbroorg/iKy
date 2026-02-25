import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Venmo module.
 *
 * Reads 3 visualizations from `result.graphic[0..2]`:
 *  0 venmo   — Force graph (profile info, gather format)
 *  1 friends — Force graph (friends network, gather format)
 *  2 trans   — DataTable (transactions)
 */
export function VenmoRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Venmo profile force graph
  const venmoData = gfx<GatherItem[]>(graphic, 0, "venmo");
  const venmoGraph = venmoData ? gatherToGraph(venmoData) : null;

  // 1 — Friends network force graph
  const friendsData = gfx<GatherItem[]>(graphic, 1, "friends");
  const friendsGraph = friendsData ? gatherToGraph(friendsData) : null;

  // 2 — Transactions data table
  const transData = gfx<
    { date: string; sender: string; receiver: string; note: string }[]
  >(graphic, 2, "trans");

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

      {/* Friends network graph — spans 2 cols */}
      {friendsGraph && friendsGraph.nodes.length >= 2 && (
        <VizCard title="Friends" className="md:col-span-2">
          <ForceGraph
            nodes={friendsGraph.nodes}
            links={friendsGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Transactions table — spans full width */}
      {transData && transData.length > 0 && (
        <VizCard
          title="Transactions"
          className="lg:col-span-3 md:col-span-2"
        >
          <DataTable data={transData} searchable pageSize={10} />
        </VizCard>
      )}
    </div>
  );
}

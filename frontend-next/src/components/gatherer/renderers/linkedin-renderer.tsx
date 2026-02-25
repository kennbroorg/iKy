import { BubbleChart } from "@/components/viz/bubble-chart";
import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the LinkedIn module.
 *
 * Reads 4 visualizations from `result.graphic[0..3]`:
 *  0 linkedin  — Force graph (gather format)
 *  1 skill     — BubbleChart (skills by endorsement)
 *  2 pos       — DataTable (positions)
 *  3 certs     — DataTable (certifications)
 */
export function LinkedinRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — LinkedIn force graph
  const linkedinData = gfx<GatherItem[]>(graphic, 0, "linkedin");
  const linkedinGraph = linkedinData ? gatherToGraph(linkedinData) : null;

  // 1 — Skills bubble chart
  const skillData = gfx<{ name: string; value: number }[]>(
    graphic,
    1,
    "skill",
  );

  // 2 — Positions data table
  const posData = gfx<Record<string, unknown>[]>(graphic, 2, "pos");

  // 3 — Certifications data table
  const certsData = gfx<Record<string, unknown>[]>(graphic, 3, "certs");

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* LinkedIn social graph — spans 2 cols */}
      {linkedinGraph && linkedinGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={linkedinGraph.nodes}
            links={linkedinGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Skills bubble chart */}
      {skillData && skillData.length > 0 && (
        <VizCard title="Skills">
          <BubbleChart data={skillData} />
        </VizCard>
      )}

      {/* Positions table — spans full width */}
      {posData && posData.length > 0 && (
        <VizCard title="Positions" className="lg:col-span-3 md:col-span-2">
          <DataTable data={posData} searchable pageSize={10} />
        </VizCard>
      )}

      {/* Certifications table — spans full width */}
      {certsData && certsData.length > 0 && (
        <VizCard title="Certifications" className="lg:col-span-3 md:col-span-2">
          <DataTable data={certsData} searchable pageSize={10} />
        </VizCard>
      )}
    </div>
  );
}

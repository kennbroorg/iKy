import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Keybase module.
 *
 * Reads 3 visualizations from `result.graphic[0..2]`:
 *  0 keybase — Force graph (profile info, gather format)
 *  1 devices — Force graph (devices, gather format)
 *  2 social  — Force graph (social proofs, gather format)
 */
export function KeybaseRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Keybase profile force graph
  const keybaseData = gfx<GatherItem[]>(graphic, 0, "keybase");
  const keybaseGraph = keybaseData ? gatherToGraph(keybaseData) : null;

  // 1 — Devices force graph
  const devicesData = gfx<GatherItem[]>(graphic, 1, "devices");
  const devicesGraph = devicesData ? gatherToGraph(devicesData) : null;

  // 2 — Social proofs force graph
  const socialData = gfx<GatherItem[]>(graphic, 2, "social");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Keybase profile graph — spans 2 cols */}
      {keybaseGraph && keybaseGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={keybaseGraph.nodes}
            links={keybaseGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Devices graph */}
      {devicesGraph && devicesGraph.nodes.length >= 2 && (
        <VizCard title="Devices">
          <ForceGraph
            nodes={devicesGraph.nodes}
            links={devicesGraph.links}
            height={300}
          />
        </VizCard>
      )}

      {/* Social proofs graph — spans 2 cols */}
      {socialGraph && socialGraph.nodes.length >= 2 && (
        <VizCard title="Social Proofs" className="md:col-span-2">
          <ForceGraph
            nodes={socialGraph.nodes}
            links={socialGraph.links}
            height={350}
          />
        </VizCard>
      )}
    </div>
  );
}

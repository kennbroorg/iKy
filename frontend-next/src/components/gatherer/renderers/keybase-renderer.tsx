import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfxByKey } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Keybase module.
 *
 * Backend `graphic.append()` calls (conditional — indices unstable):
 *  {"keysocial": social}   — only if len(social) > 1
 *  {"devices":   devices}  — only if len(devices) > 1
 *  {"keygraph":  graph}    — only if len(graph) > 1
 *
 * All three are gather-format arrays rendered as force graphs.
 * Uses key-based lookup since conditional appends make indices unstable.
 */
export function KeybaseRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // keysocial — Social proofs force graph (conditional)
  const socialData = gfxByKey<GatherItem[]>(graphic, "keysocial");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  // devices — Devices force graph (conditional)
  const devicesData = gfxByKey<GatherItem[]>(graphic, "devices");
  const devicesGraph = devicesData ? gatherToGraph(devicesData) : null;

  // keygraph — Profile info force graph (conditional)
  const keyGraphData = gfxByKey<GatherItem[]>(graphic, "keygraph");
  const keyGraph = keyGraphData ? gatherToGraph(keyGraphData) : null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Profile graph — spans 2 cols */}
      {keyGraph && keyGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={keyGraph.nodes}
            links={keyGraph.links}
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

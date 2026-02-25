import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Factory for modules with a single force graph visualization.
 *
 * Each simple module stores its gather-format data under
 * `result.graphic[0][graphKey]`.
 */
function makeSimpleRenderer(graphKey: string, title: string) {
  return function SimpleRenderer({ result }: RendererProps) {
    const data = gfx<GatherItem[]>(result.graphic, 0, graphKey);
    const graph = data ? gatherToGraph(data) : null;

    if (!graph || graph.nodes.length < 2) return null;

    return (
      <VizCard title={title}>
        <ForceGraph nodes={graph.nodes} links={graph.links} height={350} />
      </VizCard>
    );
  };
}

/** Renderer for the GitLab module — single profile force graph. */
export const GitlabRenderer = makeSimpleRenderer("gitlab", "GitLab Profile");

/** Renderer for the Tinder module — single profile force graph. */
export const TinderRenderer = makeSimpleRenderer("tinder", "Tinder Profile");

/** Renderer for the GhostProject module — single force graph. */
export const GhostprojectRenderer = makeSimpleRenderer(
  "ghostproject",
  "GhostProject",
);

/**
 * Renderer for the Skype module.
 *
 * Skype module reports a found/not-found status rather than
 * providing graph data, so we display a simple status text.
 */
export function SkypeRenderer({ result }: RendererProps) {
  const { raw } = result;
  const status =
    typeof raw === "object" && raw !== null && !Array.isArray(raw) && "status" in raw
      ? String((raw as Record<string, unknown>).status)
      : "Unknown";

  return (
    <VizCard title="Skype">
      <p className="text-sm text-foreground">{status}</p>
    </VizCard>
  );
}

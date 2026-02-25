import { ContributionCalendar } from "@/components/viz/contribution-calendar";
import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the GitHub module.
 *
 * Reads 2 visualizations from `result.graphic[0..1]`:
 *  0 github     — Force graph (profile info nodes, gather format)
 *  1 cal_actual — ContributionCalendar heatmap (raw HTML string)
 */
export function GithubRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — GitHub profile force graph
  const githubData = gfx<GatherItem[]>(graphic, 0, "github");
  const githubGraph = githubData ? gatherToGraph(githubData) : null;

  // 1 — Contribution calendar (raw HTML from scraper)
  const calHtml = gfx<string>(graphic, 1, "cal_actual");

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* GitHub profile graph — spans 2 cols */}
      {githubGraph && githubGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={githubGraph.nodes}
            links={githubGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Contribution calendar heatmap — spans 2 cols */}
      {calHtml && (
        <VizCard title="Contributions" className="md:col-span-2">
          <ContributionCalendar htmlData={calHtml} />
        </VizCard>
      )}
    </div>
  );
}

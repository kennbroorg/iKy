import { BubbleChart } from "@/components/viz/bubble-chart";
import { ForceGraph } from "@/components/viz/force-graph";
import { ModuleChart } from "@/components/viz/module-chart";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Reddit module.
 *
 * Reads 4 visualizations from `result.graphic[0..3]`:
 *  0 reddit  — Force graph (gather format)
 *  1 bubble  — BubbleChart (subreddit topics)
 *  2 hour    — Bar chart
 *  3 week    — Bar chart
 */
export function RedditRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Reddit force graph
  const redditData = gfx<GatherItem[]>(graphic, 0, "reddit");
  const redditGraph = redditData ? gatherToGraph(redditData) : null;

  // 1 — Subreddit topics bubble chart
  const bubbleData = gfx<{ name: string; value: number }[]>(
    graphic,
    1,
    "bubble",
  );

  // 2 — Hour bar chart
  const hourData = gfx<{ name: string; value: number }[]>(
    graphic,
    2,
    "hour",
  );

  // 3 — Week bar chart
  const weekData = gfx<{ name: string; value: number }[]>(
    graphic,
    3,
    "week",
  );

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Reddit social graph — spans 2 cols */}
      {redditGraph && redditGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={redditGraph.nodes}
            links={redditGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Subreddit topics bubble chart */}
      {bubbleData && bubbleData.length > 0 && (
        <VizCard title="Subreddit Topics">
          <BubbleChart data={bubbleData} />
        </VizCard>
      )}

      {/* Hour bar chart */}
      {hourData && hourData.length > 0 && (
        <VizCard title="Activity by Hour">
          <ModuleChart data={hourData} type="bar" height={200} />
        </VizCard>
      )}

      {/* Week bar chart */}
      {weekData && weekData.length > 0 && (
        <VizCard title="Activity by Day of Week">
          <ModuleChart data={weekData} type="bar" height={200} />
        </VizCard>
      )}
    </div>
  );
}

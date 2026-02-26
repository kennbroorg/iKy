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
 *  0 social — Force graph (gather format)
 *  1 hour   — Bar chart (activity by hour)
 *  2 week   — Bar chart (activity by day of week)
 *  3 topics — BubbleChart (subreddit topics, object with children[])
 */
export function RedditRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Reddit force graph (key: "social")
  const redditData = gfx<GatherItem[]>(graphic, 0, "social");
  const redditGraph = redditData ? gatherToGraph(redditData) : null;

  // 1 — Hour bar chart (key: "hour")
  const hourData = gfx<{ name: string; value: number }[]>(
    graphic,
    1,
    "hour",
  );

  // 2 — Week bar chart (key: "week")
  const weekData = gfx<{ name: string; value: number }[]>(
    graphic,
    2,
    "week",
  );

  // 3 — Subreddit topics bubble chart (key: "topics")
  // Backend produces { name: "", value: 100, children: [{name, count, value}] }
  const topicsData = gfx<{
    name: string;
    value: number;
    children: { name: string; count: number; value: number }[];
  }>(graphic, 3, "topics");
  const bubbleData = topicsData?.children;

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

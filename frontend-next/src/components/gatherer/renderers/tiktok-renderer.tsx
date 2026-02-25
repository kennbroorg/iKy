import { ForceGraph } from "@/components/viz/force-graph";
import { ModuleChart } from "@/components/viz/module-chart";
import { TreemapChart } from "@/components/viz/treemap-chart";
import { WordCloud } from "@/components/viz/word-cloud";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the TikTok module.
 *
 * Reads 8 visualizations from `result.graphic[0..7]`:
 *  0 tiktok   — Force graph (gather format)
 *  1 resume   — Treemap (children[])
 *  2 posts    — Line chart (multi-series)
 *  3 hashtag  — Word cloud
 *  4 hour     — Bar chart
 *  5 week     — Bar chart
 *  6 videos   — Force graph (thumbnails)
 *  7 time     — Bar chart (timeline)
 */
export function TiktokRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — TikTok force graph
  const tiktokData = gfx<GatherItem[]>(graphic, 0, "tiktok");
  const tiktokGraph = tiktokData ? gatherToGraph(tiktokData) : null;

  // 1 — Resume treemap
  const resumeData = gfx<{ children: { name: string; total: number }[] }>(
    graphic,
    1,
    "resume",
  );
  const treemapChildren = resumeData?.children;

  // 2 — Posts line chart (multi-series)
  const postsData = gfx<Record<string, unknown>[]>(graphic, 2, "posts");

  // 3 — Hashtag word cloud
  const hashtagData = gfx<{ label: string; value: number }[]>(
    graphic,
    3,
    "hashtag",
  );
  const hashtagWords = hashtagData?.map((h) => ({
    text: h.label,
    value: h.value,
  }));

  // 4 — Hour bar chart
  const hourData = gfx<Record<string, unknown>[]>(graphic, 4, "hour");

  // 5 — Week bar chart
  const weekData = gfx<Record<string, unknown>[]>(graphic, 5, "week");

  // 6 — Videos force graph (thumbnails)
  const videosData = gfx<GatherItem[]>(graphic, 6, "videos");
  const videosGraph = videosData ? gatherToGraph(videosData) : null;

  // 7 — Time bar chart (timeline)
  const timeData = gfx<Record<string, unknown>[]>(graphic, 7, "time");

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* TikTok social graph — spans 2 cols */}
      {tiktokGraph && tiktokGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={tiktokGraph.nodes}
            links={tiktokGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Resume treemap */}
      {treemapChildren && treemapChildren.length > 0 && (
        <VizCard title="Resume">
          <TreemapChart data={treemapChildren} height={250} />
        </VizCard>
      )}

      {/* Posts line chart — spans 2 cols */}
      {postsData && postsData.length > 0 && (
        <VizCard title="Post Activity" className="md:col-span-2">
          <ModuleChart data={postsData} type="line" height={300} />
        </VizCard>
      )}

      {/* Hashtag word cloud */}
      {hashtagWords && hashtagWords.length > 0 && (
        <VizCard title="Hashtags">
          <WordCloud words={hashtagWords} />
        </VizCard>
      )}

      {/* Hour bar chart */}
      {hourData && hourData.length > 0 && (
        <VizCard title="Activity by Hour">
          <ModuleChart data={hourData} type="bar" height={250} />
        </VizCard>
      )}

      {/* Week bar chart */}
      {weekData && weekData.length > 0 && (
        <VizCard title="Activity by Day of Week">
          <ModuleChart data={weekData} type="bar" height={250} />
        </VizCard>
      )}

      {/* Videos force graph */}
      {videosGraph && videosGraph.nodes.length >= 2 && (
        <VizCard title="Videos">
          <ForceGraph
            nodes={videosGraph.nodes}
            links={videosGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Time bar chart (timeline) */}
      {timeData && timeData.length > 0 && (
        <VizCard title="Timeline">
          <ModuleChart data={timeData} type="bar" height={250} />
        </VizCard>
      )}
    </div>
  );
}

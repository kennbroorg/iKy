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
 * Reads 10 visualizations from `result.graphic[0..9]`:
 *  0 tiktok    — Force graph (gather format)
 *  1 postslist — Line chart (multi-series: likes, comments, collect, play, repost, shared)
 *  2 hashtags  — Word cloud
 *  3 mentions  — Word cloud (currently empty in backend)
 *  4 tagged    — Word cloud (currently empty in backend)
 *  5 hour      — Bar chart
 *  6 week      — Bar chart
 *  7 videos    — Force graph (thumbnails)
 *  8 resume    — Treemap (children[])
 *  9 tiktime   — Bar chart (timeline)
 */
export function TiktokRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — TikTok force graph (key: "tiktok")
  const tiktokData = gfx<GatherItem[]>(graphic, 0, "tiktok");
  const tiktokGraph = tiktokData ? gatherToGraph(tiktokData) : null;

  // 1 — Posts line chart (key: "postslist", multi-series)
  const postslistData = gfx<Record<string, unknown>[]>(
    graphic,
    1,
    "postslist",
  );

  // 2 — Hashtag word cloud (key: "hashtags")
  const hashtagData = gfx<{ label: string; value: number }[]>(
    graphic,
    2,
    "hashtags",
  );
  const hashtagWords = hashtagData?.map((h) => ({
    text: h.label,
    value: h.value,
  }));

  // 3 — Mentions word cloud (key: "mentions", currently empty in backend)
  const mentionData = gfx<{ label: string; value: number }[]>(
    graphic,
    3,
    "mentions",
  );
  const mentionWords = mentionData?.map((m) => ({
    text: m.label,
    value: m.value,
  }));

  // 4 — Tagged word cloud (key: "tagged", currently empty in backend)
  const taggedData = gfx<{ label: string; value: number }[]>(
    graphic,
    4,
    "tagged",
  );
  const taggedWords = taggedData?.map((t) => ({
    text: t.label,
    value: t.value,
  }));

  // 5 — Hour bar chart (key: "hour")
  const hourData = gfx<Record<string, unknown>[]>(graphic, 5, "hour");

  // 6 — Week bar chart (key: "week")
  const weekData = gfx<Record<string, unknown>[]>(graphic, 6, "week");

  // 7 — Videos force graph (key: "videos")
  const videosData = gfx<GatherItem[]>(graphic, 7, "videos");
  const videosGraph = videosData ? gatherToGraph(videosData) : null;

  // 8 — Resume treemap (key: "resume")
  const resumeData = gfx<{ children: { name: string; total: number }[] }>(
    graphic,
    8,
    "resume",
  );
  const treemapChildren = resumeData?.children;

  // 9 — Timeline bar chart (key: "tiktime")
  const timeData = gfx<Record<string, unknown>[]>(graphic, 9, "tiktime");

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
      {postslistData && postslistData.length > 0 && (
        <VizCard title="Post Activity" className="md:col-span-2">
          <ModuleChart data={postslistData} type="line" height={300} />
        </VizCard>
      )}

      {/* Hashtag word cloud */}
      {hashtagWords && hashtagWords.length > 0 && (
        <VizCard title="Hashtags">
          <WordCloud words={hashtagWords} />
        </VizCard>
      )}

      {/* Mention word cloud */}
      {mentionWords && mentionWords.length > 0 && (
        <VizCard title="Mentions">
          <WordCloud words={mentionWords} />
        </VizCard>
      )}

      {/* Tagged word cloud */}
      {taggedWords && taggedWords.length > 0 && (
        <VizCard title="Tagged Users">
          <WordCloud words={taggedWords} />
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

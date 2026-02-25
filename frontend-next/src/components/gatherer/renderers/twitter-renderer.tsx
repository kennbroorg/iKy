import { ForceGraph } from "@/components/viz/force-graph";
import { ModuleChart } from "@/components/viz/module-chart";
import { TreemapChart } from "@/components/viz/treemap-chart";
import { WordCloud } from "@/components/viz/word-cloud";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Twitter / X module.
 *
 * Reads 12 visualizations from `result.graphic[0..11]`:
 *  0 social       — Force graph (profile info)
 *  1 resume       — Treemap (children[])
 *  2 popularity   — Donut chart
 *  3 approval     — Donut chart
 *  4 hashtag      — Word cloud
 *  5 users        — Force graph (mentioned users)
 *  6 tweetslist   — Line chart (multi-series)
 *  7 week         — Bar chart
 *  8 hour         — Bar chart
 *  9 sources      — Horizontal bar chart
 * 10 time         — Bar chart (timeline)
 * 11 twvsrt       — Full pie chart
 */
export function TwitterRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Social force graph
  const socialData = gfx<GatherItem[]>(graphic, 0, "social");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  // 1 — Resume treemap
  const resumeData = gfx<{ children: { name: string; total: number }[] }>(
    graphic,
    1,
    "resume",
  );
  const treemapChildren = resumeData?.children;

  // 2 — Popularity donut
  const popularityData = gfx<{ title: string; value: number }[]>(
    graphic,
    2,
    "popularity",
  );
  const popularityChart = popularityData?.map((d) => ({
    name: d.title,
    value: d.value,
  }));

  // 3 — Approval donut
  const approvalData = gfx<{ title: string; value: number }[]>(
    graphic,
    3,
    "approval",
  );
  const approvalChart = approvalData?.map((d) => ({
    name: d.title,
    value: d.value,
  }));

  // 4 — Hashtag word cloud
  const hashtagData = gfx<{ label: string; value: number }[]>(
    graphic,
    4,
    "hashtag",
  );
  const hashtagWords = hashtagData?.map((h) => ({
    text: h.label,
    value: h.value,
  }));

  // 5 — Mentioned users force graph
  const usersData = gfx<GatherItem[]>(graphic, 5, "users");
  const usersGraph = usersData ? gatherToGraph(usersData) : null;

  // 6 — Tweets list line chart (multi-series)
  const tweetslistData = gfx<Record<string, unknown>[]>(
    graphic,
    6,
    "tweetslist",
  );

  // 7 — Week bar chart
  const weekData = gfx<Record<string, unknown>[]>(graphic, 7, "week");

  // 8 — Hour bar chart
  const hourData = gfx<Record<string, unknown>[]>(graphic, 8, "hour");

  // 9 — Sources horizontal bar chart
  const sourcesData = gfx<Record<string, unknown>[]>(graphic, 9, "sources");

  // 10 — Time bar chart (timeline)
  const timeData = gfx<Record<string, unknown>[]>(graphic, 10, "time");

  // 11 — Tweets vs Retweets full pie
  const twvsrtData = gfx<{ title: string; value: number }[]>(
    graphic,
    11,
    "twvsrt",
  );
  const twvsrtChart = twvsrtData?.map((d) => ({
    name: d.title,
    value: d.value,
  }));

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Social graph — spans 2 cols */}
      {socialGraph && socialGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={socialGraph.nodes}
            links={socialGraph.links}
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

      {/* Popularity donut */}
      {popularityChart && popularityChart.length > 0 && (
        <VizCard title="Popularity">
          <ModuleChart
            data={popularityChart}
            type="pie"
            variant="donut"
            height={250}
          />
        </VizCard>
      )}

      {/* Approval donut */}
      {approvalChart && approvalChart.length > 0 && (
        <VizCard title="Approval">
          <ModuleChart
            data={approvalChart}
            type="pie"
            variant="donut"
            height={250}
          />
        </VizCard>
      )}

      {/* Hashtag word cloud */}
      {hashtagWords && hashtagWords.length > 0 && (
        <VizCard title="Hashtags">
          <WordCloud words={hashtagWords} />
        </VizCard>
      )}

      {/* Mentioned users force graph */}
      {usersGraph && usersGraph.nodes.length >= 2 && (
        <VizCard title="Mentioned Users">
          <ForceGraph
            nodes={usersGraph.nodes}
            links={usersGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Tweets list line chart — spans 2 cols */}
      {tweetslistData && tweetslistData.length > 0 && (
        <VizCard title="Tweet Activity" className="md:col-span-2">
          <ModuleChart data={tweetslistData} type="line" height={300} />
        </VizCard>
      )}

      {/* Week bar chart */}
      {weekData && weekData.length > 0 && (
        <VizCard title="Activity by Day of Week">
          <ModuleChart data={weekData} type="bar" height={250} />
        </VizCard>
      )}

      {/* Hour bar chart */}
      {hourData && hourData.length > 0 && (
        <VizCard title="Activity by Hour">
          <ModuleChart data={hourData} type="bar" height={250} />
        </VizCard>
      )}

      {/* Sources horizontal bar chart */}
      {sourcesData && sourcesData.length > 0 && (
        <VizCard title="Sources">
          <ModuleChart
            data={sourcesData}
            type="bar"
            layout="horizontal"
            height={300}
          />
        </VizCard>
      )}

      {/* Time bar chart (timeline) */}
      {timeData && timeData.length > 0 && (
        <VizCard title="Timeline">
          <ModuleChart data={timeData} type="bar" height={250} />
        </VizCard>
      )}

      {/* Tweets vs Retweets full pie */}
      {twvsrtChart && twvsrtChart.length > 0 && (
        <VizCard title="Tweets vs Retweets">
          <ModuleChart
            data={twvsrtChart}
            type="pie"
            variant="full-pie"
            height={250}
          />
        </VizCard>
      )}
    </div>
  );
}

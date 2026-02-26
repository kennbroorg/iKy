import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";
import { ModuleChart } from "@/components/viz/module-chart";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Twitch module.
 *
 * Reads 7 visualizations from `result.graphic[0..6]`:
 *  0 social    — Force graph (gather format)
 *  1 table     — DataTable (videos)
 *  2 duration  — Horizontal bar chart (video durations)
 *  3 thumbnail — (photos, not rendered here)
 *  4 week      — Bar chart
 *  5 hour      — Bar chart
 *  6 time      — Bar chart (streams over time)
 */
export function TwitchRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Twitch force graph
  const twitchData = gfx<GatherItem[]>(graphic, 0, "social");
  const twitchGraph = twitchData ? gatherToGraph(twitchData) : null;

  // 1 — Video list data table
  const listData = gfx<Record<string, unknown>[]>(graphic, 1, "table");

  // 2 — Duration horizontal bar chart
  const durationData = gfx<{ name: string; value: number }[]>(
    graphic,
    2,
    "duration",
  );

  // 3 — thumbnail (not rendered)

  // 4 — Week bar chart
  const weekData = gfx<{ name: string; value: number }[]>(
    graphic,
    4,
    "week",
  );

  // 5 — Hour bar chart
  const hourData = gfx<{ name: string; value: number }[]>(
    graphic,
    5,
    "hour",
  );

  // 6 — Time bar chart (streams over time)
  const timeData = gfx<{ name: string; value: number }[]>(
    graphic,
    6,
    "time",
  );

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Twitch social graph — spans 2 cols */}
      {twitchGraph && twitchGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={twitchGraph.nodes}
            links={twitchGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Duration horizontal bar chart */}
      {durationData && durationData.length > 0 && (
        <VizCard title="Video Durations">
          <ModuleChart
            data={durationData}
            type="bar"
            layout="horizontal"
            height={300}
          />
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

      {/* Video list table — spans full width */}
      {listData && listData.length > 0 && (
        <VizCard title="Videos" className="lg:col-span-3 md:col-span-2">
          <DataTable data={listData} searchable pageSize={10} />
        </VizCard>
      )}

      {/* Time bar chart (streams over time) */}
      {timeData && timeData.length > 0 && (
        <VizCard title="Streams Over Time">
          <ModuleChart data={timeData} type="bar" height={200} />
        </VizCard>
      )}
    </div>
  );
}

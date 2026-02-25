import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";
import { LocationMap } from "@/components/viz/location-map";
import { ModuleChart } from "@/components/viz/module-chart";
import { WordCloud } from "@/components/viz/word-cloud";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Instagram module.
 *
 * Reads 11 visualizations from `result.graphic[0..10]`:
 *  0 instagram  — Force graph (gather format)
 *  1 popularig  — Line chart (likes/comments per post)
 *  2 mediatype  — Donut chart
 *  3 hashtag    — Word cloud
 *  4 mention    — Word cloud
 *  5 tagged     — Word cloud
 *  6 hour       — Bar chart
 *  7 week       — Bar chart
 *  8 photos     — Force graph (images as picture nodes)
 *  9 list       — DataTable
 * 10 location   — LocationMap
 */
export function InstagramRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Instagram force graph
  const igData = gfx<GatherItem[]>(graphic, 0, "instagram");
  const igGraph = igData ? gatherToGraph(igData) : null;

  // 1 — Popularity line chart (multi-series)
  const popularigData = gfx<Record<string, unknown>[]>(
    graphic,
    1,
    "popularig",
  );

  // 2 — Media type donut
  const mediatypeData = gfx<Record<string, unknown>[]>(
    graphic,
    2,
    "mediatype",
  );

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

  // 4 — Mention word cloud
  const mentionData = gfx<{ label: string; value: number }[]>(
    graphic,
    4,
    "mention",
  );
  const mentionWords = mentionData?.map((m) => ({
    text: m.label,
    value: m.value,
  }));

  // 5 — Tagged word cloud
  const taggedData = gfx<{ label: string; value: number }[]>(
    graphic,
    5,
    "tagged",
  );
  const taggedWords = taggedData?.map((t) => ({
    text: t.label,
    value: t.value,
  }));

  // 6 — Hour bar chart
  const hourData = gfx<Record<string, unknown>[]>(graphic, 6, "hour");

  // 7 — Week bar chart
  const weekData = gfx<Record<string, unknown>[]>(graphic, 7, "week");

  // 8 — Photos force graph
  const photosData = gfx<GatherItem[]>(graphic, 8, "photos");
  const photosGraph = photosData ? gatherToGraph(photosData) : null;

  // 9 — Post list data table
  const listData = gfx<Record<string, unknown>[]>(graphic, 9, "list");

  // 10 — Location map
  const locationData = gfx<{ lat: number; lng: number; label: string }[]>(
    graphic,
    10,
    "location",
  );

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Instagram social graph — spans 2 cols */}
      {igGraph && igGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={igGraph.nodes}
            links={igGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Popularity line chart — spans 2 cols */}
      {popularigData && popularigData.length > 0 && (
        <VizCard title="Post Popularity" className="md:col-span-2">
          <ModuleChart data={popularigData} type="line" height={300} />
        </VizCard>
      )}

      {/* Media type donut */}
      {mediatypeData && mediatypeData.length > 0 && (
        <VizCard title="Media Types">
          <ModuleChart
            data={mediatypeData}
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

      {/* Photos force graph */}
      {photosGraph && photosGraph.nodes.length >= 2 && (
        <VizCard title="Photos">
          <ForceGraph
            nodes={photosGraph.nodes}
            links={photosGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Post list table — spans full width */}
      {listData && listData.length > 0 && (
        <VizCard title="Posts" className="lg:col-span-3 md:col-span-2">
          <DataTable data={listData} searchable pageSize={10} />
        </VizCard>
      )}

      {/* Location map — spans full width */}
      {locationData && locationData.length > 0 && (
        <VizCard title="Locations" className="lg:col-span-3 md:col-span-2">
          <LocationMap locations={locationData} height="400px" />
        </VizCard>
      )}
    </div>
  );
}

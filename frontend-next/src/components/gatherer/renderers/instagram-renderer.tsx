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
 * Reads 10 visualizations from `result.graphic[0..9]`:
 *  0 instagram — Force graph (gather format)
 *  1 postslist — Line chart (likes/comments per post, multi-series)
 *  2 postsloc  — LocationMap (post locations)
 *  3 hashtags  — Word cloud
 *  4 mentions  — Word cloud
 *  5 tagged    — Word cloud
 *  6 hour      — Bar chart
 *  7 week      — Bar chart
 *  8 mediatype — Donut chart
 *  9 photos    — Force graph (images as picture nodes)
 */
export function InstagramRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Instagram force graph (key: "instagram")
  const igData = gfx<GatherItem[]>(graphic, 0, "instagram");
  const igGraph = igData ? gatherToGraph(igData) : null;

  // 1 — Popularity line chart (key: "postslist", multi-series)
  const postslistData = gfx<Record<string, unknown>[]>(
    graphic,
    1,
    "postslist",
  );

  // 2 — Post locations (key: "postsloc")
  const postslocData = gfx<{ lat: number; lng: number; label: string }[]>(
    graphic,
    2,
    "postsloc",
  );

  // 3 — Hashtag word cloud (key: "hashtags")
  const hashtagData = gfx<{ label: string; value: number }[]>(
    graphic,
    3,
    "hashtags",
  );
  const hashtagWords = hashtagData?.map((h) => ({
    text: h.label,
    value: h.value,
  }));

  // 4 — Mention word cloud (key: "mentions")
  const mentionData = gfx<{ label: string; value: number }[]>(
    graphic,
    4,
    "mentions",
  );
  const mentionWords = mentionData?.map((m) => ({
    text: m.label,
    value: m.value,
  }));

  // 5 — Tagged word cloud (key: "tagged")
  const taggedData = gfx<{ label: string; value: number }[]>(
    graphic,
    5,
    "tagged",
  );
  const taggedWords = taggedData?.map((t) => ({
    text: t.label,
    value: t.value,
  }));

  // 6 — Hour bar chart (key: "hour")
  const hourData = gfx<Record<string, unknown>[]>(graphic, 6, "hour");

  // 7 — Week bar chart (key: "week")
  const weekData = gfx<Record<string, unknown>[]>(graphic, 7, "week");

  // 8 — Media type donut (key: "mediatype")
  const mediatypeData = gfx<Record<string, unknown>[]>(
    graphic,
    8,
    "mediatype",
  );

  // 9 — Photos force graph (key: "photos")
  const photosData = gfx<GatherItem[]>(graphic, 9, "photos");
  const photosGraph = photosData ? gatherToGraph(photosData) : null;

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
      {postslistData && postslistData.length > 0 && (
        <VizCard title="Post Popularity" className="md:col-span-2">
          <ModuleChart data={postslistData} type="line" height={300} />
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

      {/* Location map — spans full width */}
      {postslocData && postslocData.length > 0 && (
        <VizCard title="Locations" className="lg:col-span-3 md:col-span-2">
          <LocationMap locations={postslocData} height="400px" />
        </VizCard>
      )}
    </div>
  );
}

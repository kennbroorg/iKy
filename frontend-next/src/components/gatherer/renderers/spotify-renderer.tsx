import { BubbleChart } from "@/components/viz/bubble-chart";
import { ForceGraph } from "@/components/viz/force-graph";
import { ModuleChart } from "@/components/viz/module-chart";
import { WordCloud } from "@/components/viz/word-cloud";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Spotify module.
 *
 * Reads 5 visualizations from `result.graphic[0..4]`:
 *  0 social    — Force graph (gather format)
 *  1 playlist  — Horizontal bar chart
 *  2 autors    — Word cloud (artists)
 *  3 words     — Word cloud (track words)
 *  4 lang      — BubbleChart (music languages)
 */
export function SpotifyRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Spotify force graph
  const spotifyData = gfx<GatherItem[]>(graphic, 0, "social");
  const spotifyGraph = spotifyData ? gatherToGraph(spotifyData) : null;

  // 1 — Playlists horizontal bar chart
  const playlistsData = gfx<{ name: string; value: number }[]>(
    graphic,
    1,
    "playlist",
  );

  // 2 — Artists word cloud
  const autorsData = gfx<{ label: string; value: number }[]>(
    graphic,
    2,
    "autors",
  );
  const autorsWords = autorsData?.map((h) => ({
    text: h.label,
    value: h.value,
  }));

  // 3 — Track words word cloud
  const wordsData = gfx<{ label: string; value: number }[]>(
    graphic,
    3,
    "words",
  );
  const trackWords = wordsData?.map((h) => ({
    text: h.label,
    value: h.value,
  }));

  // 4 — Languages bubble chart
  const langData = gfx<{ name: string; value: number }[]>(
    graphic,
    4,
    "lang",
  );

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Spotify social graph — spans 2 cols */}
      {spotifyGraph && spotifyGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={spotifyGraph.nodes}
            links={spotifyGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Playlists horizontal bar chart */}
      {playlistsData && playlistsData.length > 0 && (
        <VizCard title="Playlists">
          <ModuleChart
            data={playlistsData}
            type="bar"
            layout="horizontal"
            height={300}
          />
        </VizCard>
      )}

      {/* Languages bubble chart */}
      {langData && langData.length > 0 && (
        <VizCard title="Music Languages">
          <BubbleChart data={langData} />
        </VizCard>
      )}

      {/* Artists word cloud */}
      {autorsWords && autorsWords.length > 0 && (
        <VizCard title="Artists">
          <WordCloud words={autorsWords} />
        </VizCard>
      )}

      {/* Track words word cloud */}
      {trackWords && trackWords.length > 0 && (
        <VizCard title="Track Words">
          <WordCloud words={trackWords} />
        </VizCard>
      )}
    </div>
  );
}

import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";
import { WordCloud } from "@/components/viz/word-cloud";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Shared renderer for the Search and Dorks modules.
 * Both share the exact same layout with 9 visualizations.
 *
 * Reads from `result.graphic[0..7]`:
 *  0 names      — Word cloud (name frequencies)
 *  1 username   — Word cloud (username frequencies)
 *  2 social     — Force graph (gather format)
 *  3 rawresults — DataTable (all raw results)
 *  4 searches   — DataTable (analyzed/filtered results)
 *  5 mentions   — Word cloud (mention frequencies)
 *  6 hashtags   — Word cloud (hashtag frequencies)
 *  7 emails     — Word cloud (email frequencies)
 *
 * Layout:
 *  Row 1: Names cloud (col-4), Social graph (col-4), Usernames cloud (col-4)
 *  Row 2: Analyzed list (col-6), Raw list (col-6)
 *  Row 3: Mentions cloud (col-4), Hashtags cloud (col-4), Emails cloud (col-4)
 */
export function SearchResultRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Names word cloud
  const namesData = gfx<{ label: string; value: number }[]>(
    graphic,
    0,
    "names",
  );
  const namesWords = namesData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  // 1 — Usernames word cloud
  const usernameData = gfx<{ label: string; value: number }[]>(
    graphic,
    1,
    "username",
  );
  const usernameWords = usernameData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  // 2 — Social force graph
  const socialData = gfx<GatherItem[]>(graphic, 2, "social");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  // 3 — Raw results table
  const rawData = gfx<Record<string, unknown>[]>(graphic, 3, "rawresults");

  // 4 — Analyzed/filtered results table
  const searchesData = gfx<Record<string, unknown>[]>(graphic, 4, "searches");

  // 5 — Mentions word cloud
  const mentionsData = gfx<{ label: string; value: number }[]>(
    graphic,
    5,
    "mentions",
  );
  const mentionsWords = mentionsData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  // 6 — Hashtags word cloud
  const hashtagsData = gfx<{ label: string; value: number }[]>(
    graphic,
    6,
    "hashtags",
  );
  const hashtagsWords = hashtagsData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  // 7 — Emails word cloud
  const emailsData = gfx<{ label: string; value: number }[]>(
    graphic,
    7,
    "emails",
  );
  const emailsWords = emailsData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  return (
    <div className="space-y-4">
      {/* Row 1: Names cloud, Social graph, Usernames cloud */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {namesWords && namesWords.length > 0 && (
          <VizCard title="Names">
            <WordCloud words={namesWords} />
          </VizCard>
        )}

        {socialGraph && socialGraph.nodes.length >= 2 && (
          <VizCard title="Social">
            <ForceGraph
              nodes={socialGraph.nodes}
              links={socialGraph.links}
              height={300}
            />
          </VizCard>
        )}

        {usernameWords && usernameWords.length > 0 && (
          <VizCard title="Usernames">
            <WordCloud words={usernameWords} />
          </VizCard>
        )}
      </div>

      {/* Row 2: Analyzed list, Raw list */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {searchesData && searchesData.length > 0 && (
          <VizCard title="Analyzed Results">
            <DataTable data={searchesData} searchable pageSize={10} />
          </VizCard>
        )}

        {rawData && rawData.length > 0 && (
          <VizCard title="Raw Results">
            <DataTable data={rawData} searchable pageSize={10} />
          </VizCard>
        )}
      </div>

      {/* Row 3: Mentions cloud, Hashtags cloud, Emails cloud */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {mentionsWords && mentionsWords.length > 0 && (
          <VizCard title="Mentions">
            <WordCloud words={mentionsWords} />
          </VizCard>
        )}

        {hashtagsWords && hashtagsWords.length > 0 && (
          <VizCard title="Hashtags">
            <WordCloud words={hashtagsWords} />
          </VizCard>
        )}

        {emailsWords && emailsWords.length > 0 && (
          <VizCard title="Emails">
            <WordCloud words={emailsWords} />
          </VizCard>
        )}
      </div>
    </div>
  );
}

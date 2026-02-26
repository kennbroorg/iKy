import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";
import { WordCloud } from "@/components/viz/word-cloud";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfxByKey } from "./types";
import { VizCard } from "./viz-card";

/**
 * Shared renderer for the Search and Dorks modules.
 *
 * Search backend `graphic.append()` (9 items):
 *  0 {"names":      name_cloud}
 *  1 {"username":   username_cloud}
 *  2 {"social":     social_raw}
 *  3 {"rawresults": output["rawresult"]}
 *  4 {"results":    analized_results}      <-- search only, dorks omits this
 *  5 {"searches":   output["search"]}
 *  6 {"mentions":   output["users"]}
 *  7 {"hashtags":   output["hashtags"]}
 *  8 {"emails":     output["emails"]}
 *
 * Dorks backend `graphic.append()` (8 items — no "results"):
 *  0 {"names":      name_cloud}
 *  1 {"username":   username_cloud}
 *  2 {"social":     social_raw}
 *  3 {"rawresults": output["rawresult"]}
 *  4 {"searches":   output["search"]}
 *  5 {"mentions":   output["users"]}
 *  6 {"hashtags":   output["hashtags"]}
 *  7 {"emails":     output["emails"]}
 *
 * Uses key-based lookup to handle both modules with the same renderer,
 * since "results" at index 4 in search shifts all subsequent indices.
 *
 * Layout:
 *  Row 1: Names cloud, Social graph, Usernames cloud
 *  Row 2: Analyzed results, Raw results
 *  Row 3: Mentions cloud, Hashtags cloud, Emails cloud
 */
export function SearchResultRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // names — Word cloud (name frequencies)
  const namesData = gfxByKey<{ label: string; value: number }[]>(
    graphic,
    "names",
  );
  const namesWords = namesData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  // username — Word cloud (username frequencies)
  const usernameData = gfxByKey<{ label: string; value: number }[]>(
    graphic,
    "username",
  );
  const usernameWords = usernameData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  // social — Force graph (gather format)
  const socialData = gfxByKey<GatherItem[]>(graphic, "social");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  // rawresults — DataTable (all raw results)
  const rawData = gfxByKey<Record<string, unknown>[]>(graphic, "rawresults");

  // searches — DataTable (analyzed/filtered results)
  const searchesData = gfxByKey<Record<string, unknown>[]>(
    graphic,
    "searches",
  );

  // mentions — Word cloud (mention frequencies)
  const mentionsData = gfxByKey<{ label: string; value: number }[]>(
    graphic,
    "mentions",
  );
  const mentionsWords = mentionsData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  // hashtags — Word cloud (hashtag frequencies)
  const hashtagsData = gfxByKey<{ label: string; value: number }[]>(
    graphic,
    "hashtags",
  );
  const hashtagsWords = hashtagsData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  // emails — Word cloud (email frequencies)
  const emailsData = gfxByKey<{ label: string; value: number }[]>(
    graphic,
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

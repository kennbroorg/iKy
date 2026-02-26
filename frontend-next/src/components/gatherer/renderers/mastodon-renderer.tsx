import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the Mastodon module.
 *
 * Reads 3 visualizations from `result.graphic[0..2]`:
 *  0 user   — Force graph (profile info, gather format)
 *  1 social — Force graph (social connections, gather format)
 *  2 list   — DataTable (found accounts)
 */
export function MastodonRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — Mastodon profile force graph
  const mastodonData = gfx<GatherItem[]>(graphic, 0, "user");
  const mastodonGraph = mastodonData ? gatherToGraph(mastodonData) : null;

  // 1 — Social connections force graph
  const socialData = gfx<GatherItem[]>(graphic, 1, "social");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  // 2 — Found accounts data table
  const listData = gfx<
    { title: string; avatar: string; toots: number; followers: number; followings: number; bio: string }[]
  >(graphic, 2, "list");

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Mastodon profile graph — spans 2 cols */}
      {mastodonGraph && mastodonGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={mastodonGraph.nodes}
            links={mastodonGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Found accounts table — spans full width */}
      {listData && listData.length > 0 && (
        <VizCard title="Accounts" className="lg:col-span-3 md:col-span-2">
          <DataTable data={listData} searchable pageSize={10} />
        </VizCard>
      )}

      {/* Social connections graph — spans 2 cols */}
      {socialGraph && socialGraph.nodes.length >= 2 && (
        <VizCard title="Social Connections" className="md:col-span-2">
          <ForceGraph
            nodes={socialGraph.nodes}
            links={socialGraph.links}
            height={350}
          />
        </VizCard>
      )}
    </div>
  );
}

import { ForceGraph } from "@/components/viz/force-graph";
import { WordCloud } from "@/components/viz/word-cloud";

import type { GraphicItem } from "@/types/api";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Scan all graphic items and return the first value matching the given key.
 * Useful when optional entries shift indices (e.g. FullContact).
 */
function findByKey<T = unknown>(
  graphic: GraphicItem[],
  key: string,
): T | undefined {
  for (const item of graphic) {
    if (item[key] !== undefined) return item[key] as T;
  }
  return undefined;
}

/**
 * Renderer for the EmailRep module.
 *
 * Backend graphic.append() calls (emailrep_tasks.py):
 *  0 details — Force graph (gather items: reputation flags, blacklisted, spam, etc.)
 *  1 social  — Force graph (associated social profiles) — optional, only if profiles found
 */
export function EmailRepRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — EmailRep reputation details force graph (key: "details")
  const detailsData = gfx<GatherItem[]>(graphic, 0, "details");
  const detailsGraph = detailsData ? gatherToGraph(detailsData) : null;

  // 1 — Social profiles force graph (key: "social", optional)
  const socialData = gfx<GatherItem[]>(graphic, 1, "social");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* EmailRep reputation details graph — spans 2 cols */}
      {detailsGraph && detailsGraph.nodes.length >= 2 && (
        <VizCard title="Reputation" className="md:col-span-2">
          <ForceGraph
            nodes={detailsGraph.nodes}
            links={detailsGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Social profiles graph — spans 2 cols */}
      {socialGraph && socialGraph.nodes.length >= 2 && (
        <VizCard title="Social Profiles" className="md:col-span-2">
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

/**
 * Renderer for the FullContact module.
 *
 * Backend graphic.append() calls (fullcontact_tasks.py):
 *  0 social    — Force graph (social profiles, always present)
 *  1 bios      — Bios text array (optional, only if bios found)
 *  ? photo     — Photo items (optional, only if photos found)
 *  ? webs      — Website URLs (optional, v2 API path only)
 *  ? footprint — Word cloud items ({label}[], optional, only if digital footprint found)
 *
 * Because bios/photo/webs/footprint are all optional and indices shift,
 * we scan all graphic items by key rather than using fixed indices.
 */
export function FullContactRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // Find items by key since optional entries shift indices
  const socialData = findByKey<GatherItem[]>(graphic, "social");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  const footprintData = findByKey<{ label: string }[]>(graphic, "footprint");
  const cloudWords = footprintData?.map((d, i) => ({
    text: d.label,
    value: 10 - i, // assign descending weight since backend doesn't include value
  }));

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* FullContact social profiles graph — spans 2 cols */}
      {socialGraph && socialGraph.nodes.length >= 2 && (
        <VizCard title="Social Profiles" className="md:col-span-2">
          <ForceGraph
            nodes={socialGraph.nodes}
            links={socialGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Digital footprint word cloud */}
      {cloudWords && cloudWords.length > 0 && (
        <VizCard title="Digital Footprint">
          <WordCloud words={cloudWords} />
        </VizCard>
      )}
    </div>
  );
}

/**
 * Renderer for the PeopleDataLabs module.
 *
 * Backend graphic.append() calls (peopledatalabs_tasks.py):
 *  0 data   — Force graph (enriched profile: name, company, location, industry, etc.)
 *  1 social — Force graph (social profiles from PDL)
 */
export function PeopleDataLabsRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — PeopleDataLabs enriched profile force graph (key: "data")
  const pdlData = gfx<GatherItem[]>(graphic, 0, "data");
  const pdlGraph = pdlData ? gatherToGraph(pdlData) : null;

  // 1 — Social profiles force graph (key: "social")
  const socialData = gfx<GatherItem[]>(graphic, 1, "social");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* PeopleDataLabs profile graph — spans 2 cols */}
      {pdlGraph && pdlGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={pdlGraph.nodes}
            links={pdlGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Social profiles graph — spans 2 cols */}
      {socialGraph && socialGraph.nodes.length >= 2 && (
        <VizCard title="Social Profiles" className="md:col-span-2">
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

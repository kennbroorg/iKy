import { ForceGraph } from "@/components/viz/force-graph";
import { WordCloud } from "@/components/viz/word-cloud";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Renderer for the EmailRep module.
 *
 * Reads 2 visualizations from `result.graphic[0..1]`:
 *  0 emailrep — Force graph (reputation details: malicious flags, spam score, etc.)
 *  1 social   — Force graph (associated social profiles)
 */
export function EmailRepRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — EmailRep reputation force graph
  const emailrepData = gfx<GatherItem[]>(graphic, 0, "emailrep");
  const emailrepGraph = emailrepData ? gatherToGraph(emailrepData) : null;

  // 1 — Social profiles force graph
  const socialData = gfx<GatherItem[]>(graphic, 1, "social");
  const socialGraph = socialData ? gatherToGraph(socialData) : null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* EmailRep reputation graph — spans 2 cols */}
      {emailrepGraph && emailrepGraph.nodes.length >= 2 && (
        <VizCard title="Reputation" className="md:col-span-2">
          <ForceGraph
            nodes={emailrepGraph.nodes}
            links={emailrepGraph.links}
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
 * Reads 2 visualizations from `result.graphic[0..1]`:
 *  0 fullcontact — Force graph (enriched profile: name, company, social profiles)
 *  1 cloud       — Word cloud (digital footprint keywords, {label, value}[])
 */
export function FullContactRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — FullContact profile force graph
  const fullcontactData = gfx<GatherItem[]>(graphic, 0, "fullcontact");
  const fullcontactGraph = fullcontactData
    ? gatherToGraph(fullcontactData)
    : null;

  // 1 — Digital footprint word cloud
  const cloudData = gfx<{ label: string; value: number }[]>(
    graphic,
    1,
    "cloud",
  );
  const cloudWords = cloudData?.map((d) => ({
    text: d.label,
    value: d.value,
  }));

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* FullContact profile graph — spans 2 cols */}
      {fullcontactGraph && fullcontactGraph.nodes.length >= 2 && (
        <VizCard title="Profile" className="md:col-span-2">
          <ForceGraph
            nodes={fullcontactGraph.nodes}
            links={fullcontactGraph.links}
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
 * Reads 2 visualizations from `result.graphic[0..1]`:
 *  0 peopledatalabs — Force graph (enriched profile)
 *  1 social         — Force graph (social profiles)
 */
export function PeopleDataLabsRenderer({ result }: RendererProps) {
  const { graphic } = result;

  // 0 — PeopleDataLabs profile force graph
  const pdlData = gfx<GatherItem[]>(graphic, 0, "peopledatalabs");
  const pdlGraph = pdlData ? gatherToGraph(pdlData) : null;

  // 1 — Social profiles force graph
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

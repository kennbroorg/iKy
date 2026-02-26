import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Factory for modules with a single force graph visualization.
 *
 * Each simple module stores its gather-format data under
 * `result.graphic[0][graphKey]`.
 */
function makeSimpleRenderer(graphKey: string, title: string) {
  return function SimpleRenderer({ result }: RendererProps) {
    const data = gfx<GatherItem[]>(result.graphic, 0, graphKey);
    const graph = data ? gatherToGraph(data) : null;

    if (!graph || graph.nodes.length < 2) return null;

    return (
      <VizCard title={title}>
        <ForceGraph nodes={graph.nodes} links={graph.links} height={350} />
      </VizCard>
    );
  };
}

/**
 * Renderer for the GitLab module.
 *
 * Backend (gitlab_tasks.py) appends an empty graphic array:
 *   total.append({"graphic": []})
 * All useful data is in `raw` (a flat string array). The module does not
 * produce any graphic items, so we display the raw details as a simple list.
 */
export function GitlabRenderer({ result }: RendererProps) {
  const raw = result.raw;
  const items = Array.isArray(raw) ? (raw as string[]) : [];

  if (items.length === 0) return null;

  return (
    <VizCard title="GitLab Profile">
      <ul className="list-inside list-disc space-y-1 text-sm text-foreground">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </VizCard>
  );
}

/** Renderer for the Tinder module — single profile force graph (key: "tinder" at index 0). */
export const TinderRenderer = makeSimpleRenderer("tinder", "Tinder Profile");

/**
 * Renderer for the GhostProject module.
 *
 * Backend (ghostproject_tasks.py) does NOT produce a graphic array at all.
 * The leak data lives at the top level: total.append({"leaks": [...]}).
 * Each leak is {email: string, password: string}.
 * We display the count plus a table of leaked credentials.
 */
export function GhostprojectRenderer({ result }: RendererProps) {
  const { leaks } = result;

  if (!leaks || leaks.length === 0) {
    return (
      <VizCard title="GhostProject">
        <p className="text-sm text-muted-foreground">No leaks found.</p>
      </VizCard>
    );
  }

  return (
    <VizCard title={`GhostProject (${leaks.length} leaks)`}>
      <div className="max-h-64 overflow-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="pb-1 pr-4">Email</th>
              <th className="pb-1">Password</th>
            </tr>
          </thead>
          <tbody>
            {leaks.map((leak, i) => (
              <tr key={i} className="border-b border-border/50">
                <td className="py-1 pr-4 font-mono text-xs">{leak.email}</td>
                <td className="py-1 font-mono text-xs">{leak.password}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </VizCard>
  );
}

/**
 * Renderer for the Skype module — single profile force graph.
 *
 * Backend (skype_tasks.py) appends: graphic.append({"skype": gather})
 * The gather array contains Skype username and status items.
 */
export const SkypeRenderer = makeSimpleRenderer("skype", "Skype");

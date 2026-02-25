import { DataTable } from "@/components/viz/data-table";
import { ForceGraph } from "@/components/viz/force-graph";

import { gatherToGraph, type GatherItem } from "./graph-helpers";
import type { RendererProps } from "./types";
import { gfx } from "./types";
import { VizCard } from "./viz-card";

/**
 * Shared layout for account-check modules (Holehe, Sherlock).
 * Left: force graph of found accounts. Right: searchable data table.
 */
function AccountCheckLayout({
  graphTitle,
  graphData,
  tableTitle,
  tableData,
}: {
  graphTitle: string;
  graphData: GatherItem[] | undefined;
  tableTitle: string;
  tableData: Record<string, unknown>[] | undefined;
}) {
  const graph = graphData ? gatherToGraph(graphData) : null;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {/* Force graph — found accounts */}
      {graph && graph.nodes.length >= 2 && (
        <VizCard title={graphTitle}>
          <ForceGraph
            nodes={graph.nodes}
            links={graph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Data table — all sites with status */}
      {tableData && tableData.length > 0 && (
        <VizCard title={tableTitle}>
          <DataTable data={tableData} searchable pageSize={10} />
        </VizCard>
      )}
    </div>
  );
}

/**
 * Renderer for the Holehe module.
 *
 * Reads 2 visualizations from `result.graphic[0..1]`:
 *  0 holehe — gather format — Force graph (found accounts)
 *  1 lists  — DataTable rows {title, exists, rateLimit, emailrecovery, phoneNumber}
 */
export function HoleheRenderer({ result }: RendererProps) {
  const { graphic } = result;

  const graphData = gfx<GatherItem[]>(graphic, 0, "holehe");
  const listData = gfx<Record<string, unknown>[]>(graphic, 1, "lists");

  return (
    <AccountCheckLayout
      graphTitle="Found Accounts"
      graphData={graphData}
      tableTitle="All Sites"
      tableData={listData}
    />
  );
}

/**
 * Renderer for the Sherlock module.
 *
 * Reads 2 visualizations from `result.graphic[0..1]`:
 *  0 sherlock — gather format — Force graph (claimed accounts)
 *  1 lists   — DataTable rows {title, subtitle, status, response}
 */
export function SherlockRenderer({ result }: RendererProps) {
  const { graphic } = result;

  const graphData = gfx<GatherItem[]>(graphic, 0, "sherlock");
  const listData = gfx<Record<string, unknown>[]>(graphic, 1, "lists");

  return (
    <AccountCheckLayout
      graphTitle="Claimed Accounts"
      graphData={graphData}
      tableTitle="All Sites"
      tableData={listData}
    />
  );
}

/**
 * Renderer for the Socialscan module.
 *
 * Reads 2 visualizations from `result.graphic[0..1]`:
 *  0 social_email — gather format — Force graph (email-registered sites)
 *  1 social_user  — gather format — Force graph (username-registered sites)
 */
export function SocialscanRenderer({ result }: RendererProps) {
  const { graphic } = result;

  const emailData = gfx<GatherItem[]>(graphic, 0, "social_email");
  const emailGraph = emailData ? gatherToGraph(emailData) : null;

  const userData = gfx<GatherItem[]>(graphic, 1, "social_user");
  const userGraph = userData ? gatherToGraph(userData) : null;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {/* Email-registered sites */}
      {emailGraph && emailGraph.nodes.length >= 2 && (
        <VizCard title="Email Registered">
          <ForceGraph
            nodes={emailGraph.nodes}
            links={emailGraph.links}
            height={350}
          />
        </VizCard>
      )}

      {/* Username-registered sites */}
      {userGraph && userGraph.nodes.length >= 2 && (
        <VizCard title="Username Registered">
          <ForceGraph
            nodes={userGraph.nodes}
            links={userGraph.links}
            height={350}
          />
        </VizCard>
      )}
    </div>
  );
}

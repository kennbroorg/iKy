import type { ComponentType } from "react";

import type { RendererProps } from "./types";

export type { RendererProps } from "./types";
export { gfx } from "./types";
export { VizCard } from "./viz-card";
export { gatherToGraph } from "./graph-helpers";
export type { GraphNode, GraphLink, GatherItem } from "./graph-helpers";

export const MODULE_RENDERERS: Record<
  string,
  ComponentType<RendererProps>
> = {
  // Will be populated by subsequent tasks
};

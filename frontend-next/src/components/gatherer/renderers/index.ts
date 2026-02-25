import type { ComponentType } from "react";

import { InstagramRenderer } from "./instagram-renderer";
import { LinkedinRenderer } from "./linkedin-renderer";
import { RedditRenderer } from "./reddit-renderer";
import { SpotifyRenderer } from "./spotify-renderer";
import { TiktokRenderer } from "./tiktok-renderer";
import { TwitchRenderer } from "./twitch-renderer";
import { TwitterRenderer } from "./twitter-renderer";
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
  twitter: TwitterRenderer,
  instagram: InstagramRenderer,
  tiktok: TiktokRenderer,
  twitch: TwitchRenderer,
  reddit: RedditRenderer,
  spotify: SpotifyRenderer,
  linkedin: LinkedinRenderer,
};

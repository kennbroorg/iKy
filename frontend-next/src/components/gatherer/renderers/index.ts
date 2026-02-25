import type { ComponentType } from "react";

import {
  HoleheRenderer,
  SherlockRenderer,
  SocialscanRenderer,
} from "./account-check-renderer";
import { GithubRenderer } from "./github-renderer";
import { InstagramRenderer } from "./instagram-renderer";
import { KeybaseRenderer } from "./keybase-renderer";
import {
  DarkpassRenderer,
  LeakGraphRenderer,
  LeakLookupRenderer,
  PsbdmpRenderer,
} from "./leak-renderer";
import { LinkedinRenderer } from "./linkedin-renderer";
import { MastodonRenderer } from "./mastodon-renderer";
import { RedditRenderer } from "./reddit-renderer";
import { SearchResultRenderer } from "./search-renderer";
import { SpotifyRenderer } from "./spotify-renderer";
import { TiktokRenderer } from "./tiktok-renderer";
import { TwitchRenderer } from "./twitch-renderer";
import { TwitterRenderer } from "./twitter-renderer";
import { VenmoRenderer } from "./venmo-renderer";
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
  mastodon: MastodonRenderer,
  keybase: KeybaseRenderer,
  venmo: VenmoRenderer,
  github: GithubRenderer,
  holehe: HoleheRenderer,
  sherlock: SherlockRenderer,
  socialscan: SocialscanRenderer,
  search: SearchResultRenderer,
  dorks: SearchResultRenderer,
  leaks: LeakGraphRenderer,
  leaklookup: LeakLookupRenderer,
  darkpass: DarkpassRenderer,
  psbdmp: PsbdmpRenderer,
};

# Module-Specific Visualizations for frontend-next

**Date:** 2026-02-25
**Branch:** `frontend-next`
**Status:** Approved

## Problem

All 28 modules in frontend-next use a generic `ResultCard` with Details/Table/Raw tabs.
The original Angular frontend has rich, module-specific visualizations for ~20 modules.
We need to bring each module to parity.

## Architecture

### Module Renderer Registry

A `moduleRenderers` map keyed by module ID. `ResultCard` checks this map first; if a
custom renderer exists, it renders that instead of the generic tabs. Custom renderers
receive the parsed `ModuleResultRaw` and render a grid of visualization cards.

```typescript
const RENDERERS: Record<string, ComponentType<RendererProps>> = {
  twitter:  TwitterRenderer,
  github:   GithubRenderer,
  holehe:   AccountCheckRenderer,
  sherlock: AccountCheckRenderer,
  // ...
};
```

### New Shared Viz Components

1. **Treemap** — Recharts treemap for profile stat breakdowns (Twitter/TikTok resume)
2. **BubbleChart** — D3 circle-pack for skill/topic distributions (LinkedIn, Spotify, Reddit)
3. **ContributionCalendar** — CSS grid heatmap (GitHub calendar, no raw HTML injection)
4. **DonutChart** — `ModuleChart` with `variant="donut"` prop for doughnut charts

### Module Renderer Grouping

| Renderer | Modules | Visualizations |
|----------|---------|----------------|
| `SocialProfileRenderer` | twitter, instagram, tiktok, twitch, reddit, spotify, mastodon, keybase, venmo, linkedin | Force graph + module-specific charts |
| `AccountCheckRenderer` | holehe, sherlock, socialscan | Force graph (found) + status list |
| `SearchResultRenderer` | search, dorks | Social graph + word clouds + result lists |
| `LeakRenderer` | leaks, leaklookup, darkpass, psbdmp | Graph/cloud + breach list |
| `EnrichmentRenderer` | emailrep, fullcontact, peopledatalabs | Force graph(s) + cloud |
| `GithubRenderer` | github | Force graph + contribution calendar |
| `SimpleGraphRenderer` | gitlab, tinder, skype, ghostproject | Force graph only |

### Data Parsing

Each custom renderer parses `graphic[]` using known positional indices from the backend
(e.g., Twitter `graphic[0].social`, `graphic[1].resume.children`). The `GraphicItem` type
supports this via `[key: string]: unknown`.

### Layout

Responsive CSS grid of visualization cards per renderer. Cards have title headers + viz.
Click-to-expand using Dialog component for full-size view.

## Deferred

- Comparison page (side-by-side Twitter period comparison)
- Text scramble animation (FullContact bios)
- 3D rotating word cloud (existing CSS word cloud covers same data)
- Per-card help popovers

## Module Visualization Map

### Twitter (12 visualizations)
- `graphic[0].social` — Force graph (profile info nodes)
- `graphic[1].resume.children` — Treemap (following/followers/tweets/likes)
- `graphic[2].popularity` — Donut chart (following vs followers ratio)
- `graphic[3].approval` — Donut chart (tweets vs likes ratio)
- `graphic[4].hashtag` — Word cloud (hashtags)
- `graphic[5].users` — Force graph (mentioned users)
- `graphic[6].tweetslist` — Line chart (retweets/likes/replies per tweet)
- `graphic[7].week` — Bar chart (activity by weekday)
- `graphic[8].hour` — Bar chart (activity by hour)
- `graphic[9].sources` — Horizontal bar chart (tweet sources/devices)
- `graphic[10].time` — Bar chart (tweets over time)
- `graphic[11].twvsrt` — Pie chart (tweets vs retweets)

### Instagram (11 visualizations)
- `graphic[0].instagram` — Force graph (profile info)
- `graphic[1].popularig` — Line chart (likes/comments per post)
- `graphic[2].mediatype` — Donut chart (photo/video/carousel)
- `graphic[3].hashtag` — Word cloud (hashtags)
- `graphic[4].mention` — Word cloud (mentions)
- `graphic[5].tagged` — Word cloud (tagged users)
- `graphic[6].hour` — Bar chart (by hour)
- `graphic[7].week` — Bar chart (by weekday)
- `graphic[8].photos` — Force graph (post images as picture nodes)
- `graphic[9].list` — List (posts with date/description/likes)
- `graphic[10].location` — Map (geolocated posts)

### TikTok (8 visualizations)
- `graphic[0].tiktok` — Force graph (profile info)
- `graphic[1].resume.children` — Treemap (following/followers/hearts/videos)
- `graphic[2].posts` — Line chart (plays/likes/comments per video)
- `graphic[3].hashtag` — Word cloud (hashtags)
- `graphic[4].hour` — Bar chart (by hour)
- `graphic[5].week` — Bar chart (by weekday)
- `graphic[6].videos` — Force graph (video thumbnails as picture nodes)
- `graphic[7].time` — Bar chart (videos over time)

### Twitch (6 visualizations)
- `graphic[0].twitch` — Force graph (profile info)
- `graphic[1].duration` — Horizontal bar chart (video durations)
- `graphic[2].hour` — Bar chart (by hour)
- `graphic[3].week` — Bar chart (by weekday)
- `graphic[4].list` — List (video titles/dates/descriptions)
- `graphic[5].time` — Bar chart (streams over time)

### Reddit (4 visualizations)
- `graphic[0].reddit` — Force graph (profile info)
- `graphic[1].bubble` — Bubble chart (subreddit topics)
- `graphic[2].hour` — Bar chart (by hour)
- `graphic[3].week` — Bar chart (by weekday)

### Spotify (5 visualizations)
- `graphic[0].spotify` — Force graph (profile info)
- `graphic[1].playlists` — Horizontal bar chart (playlists by track count)
- `graphic[2].lang` — Bubble chart (music languages)
- `graphic[3].autors` — Word cloud (artists)
- `graphic[4].words` — Word cloud (track title words)

### LinkedIn (4 visualizations)
- `graphic[0].linkedin` — Force graph (profile info)
- `graphic[1].skill` — Bubble chart (skills by endorsement)
- `graphic[2].pos` — List (job positions)
- `graphic[3].certs` — List (certifications)

### Mastodon (3 visualizations)
- `graphic[0].mastodon` — Force graph (profile info)
- `graphic[1].list` — List (accounts with avatar/toots/followers)
- `graphic[2].social` — Force graph (social connections)

### Keybase (3 visualizations)
- `graphic[0].keybase` — Force graph (profile info)
- `graphic[1].devices` — Force graph (devices)
- `graphic[2].social` — Force graph (social proofs)

### Venmo (3 visualizations)
- `graphic[0].venmo` — Force graph (profile info)
- `graphic[1].friends` — Force graph (friends network)
- `graphic[2].trans` — List (transactions)

### GitHub (2 visualizations)
- `graphic[0].github` — Force graph (profile info nodes)
- `graphic[1].cal_actual` — Contribution calendar heatmap

### Holehe (2 visualizations)
- `graphic[0].holehe` — Force graph (found sites only)
- `graphic[1].lists` — List (all sites: exists, rateLimit, emailrecovery, phoneNumber)

### Sherlock (2 visualizations)
- `graphic[0].sherlock` — Force graph (claimed sites)
- `graphic[1].lists` — List (all sites: title, URL, status code)

### Socialscan (2 visualizations)
- `graphic[0].social_email` — Force graph (email-registered platforms)
- `graphic[1].social_user` — Force graph (username-registered platforms)

### Search (9 visualizations)
- `graphic[0].names` — Word cloud
- `graphic[1].username` — Word cloud
- `graphic[2].social` — Force graph
- `graphic[3].rawresults` — List (all raw results)
- `graphic[4].searches` — List (analyzed/filtered results)
- `graphic[5].mentions` — Word cloud
- `graphic[6].hashtags` — Word cloud
- `graphic[7].emails` — Word cloud
- (search-searches component exists but is mostly unused)

### Dorks (9 visualizations — mirrors Search)
- `graphic[0].names` — Word cloud
- `graphic[1].username` — Word cloud
- `graphic[2].social` — Force graph
- `graphic[3].rawresults` — List (all raw results)
- `graphic[4].searches` — List (analyzed results)
- `graphic[5].mentions` — Word cloud
- `graphic[6].hashtags` — Word cloud
- `graphic[7].emails` — Word cloud

### Leak/HIBP (1 visualization)
- `graphic[0].leak` — Force graph (breached databases)

### LeakLookup (1 visualization)
- `graphic[0].leaklookup` — Accordion list (sites with leaked field names/values)

### Darkpass (1 visualization)
- `graphic[0].darkpass` — List (leaked passwords)

### PsbDmp (2 visualizations)
- `graphic[0].psbdmp` — Word cloud (paste content words)
- `graphic[1].list` — List (paste entries with time/ID/tags)

### EmailRep (2 visualizations)
- `graphic[0].emailrep` — Force graph (reputation details)
- `graphic[1].social` — Force graph (associated social profiles)

### FullContact (2 visualizations, skip text scramble)
- `graphic[0].fullcontact` — Force graph (enriched profile)
- `graphic[1].cloud` — Word cloud (digital footprint)

### PeopleDataLabs (2 visualizations)
- `graphic[0].peopledatalabs` — Force graph (enriched profile)
- `graphic[1].social` — Force graph (social profiles)

### Simple modules (force graph only)
- GitLab: `graphic[0].gitlab`
- Tinder: `graphic[0].tinder`
- Skype: status text only
- GhostProject: `graphic[0].ghostproject`

# New Frontend Design — React + Vite + shadcn/ui

**Date**: 2026-02-25
**Status**: Approved
**Goal**: Build a new frontend with usability parity, modern stack, dark hacker aesthetic, coexisting alongside the current Angular frontend in a separate container.

---

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | React 19 + TypeScript | Best viz ecosystem, strong types |
| Build | Vite 6 | Instant HMR, fast builds |
| Routing | React Router 7 | Standard SPA routing |
| State | Zustand | Minimal boilerplate, great DX |
| Server state | TanStack Query | Polling, caching, WS invalidation |
| Styling | Tailwind CSS 4 | Utility-first, easy dark theme |
| Components | shadcn/ui | Copy-paste, fully customizable |
| Charts | Recharts | React-native charting |
| Network graphs | react-force-graph-2d | D3-force with React wrapper |
| Maps | react-leaflet | Same Leaflet engine as today |
| Tables | TanStack Table | Headless, full control |
| WebSocket | Socket.IO client | Real-time task updates |
| Icons | Lucide React + react-icons | shadcn default + social icons |
| Forms | React Hook Form + Zod | Validation for search/API keys |
| Testing | Vitest + Testing Library + Playwright + MSW | Unit, component, e2e, API mocking |

---

## Project Structure

```
frontend-next/
├── src/
│   ├── app/             # Root layout, providers, global styles
│   ├── pages/           # Route pages
│   │   ├── gatherer/    # Main search + module results
│   │   ├── profile/     # Aggregated profile view
│   │   ├── timeline/    # Chronological events
│   │   └── apikeys/     # API key management
│   ├── components/
│   │   ├── ui/          # shadcn/ui components (button, card, dialog, etc.)
│   │   ├── layout/      # Sidebar, Header, Footer
│   │   ├── viz/         # Reusable: ForceGraph, Charts, WordCloud, Map, DataTable
│   │   └── modules/     # Custom components only for unique module viz
│   ├── hooks/           # useModuleQuery, useWebSocket, useTheme
│   ├── lib/             # API client, socket client, utilities
│   ├── stores/          # Zustand: gatherStore, apiKeyStore, uiStore
│   └── types/           # TypeScript types for API responses, modules
├── public/              # Static assets (logo, geojson)
├── Dockerfile
├── nginx.conf
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   React App                      │
│                                                  │
│  ┌───────────┐   ┌──────────┐   ┌────────────┐ │
│  │  Pages     │   │  Stores  │   │ TanStack   │ │
│  │ (routes)   │──▶│ (Zustand)│◀──│ Query      │ │
│  └───────────┘   └──────────┘   └─────┬──────┘ │
│        │                              │         │
│        ▼                              ▼         │
│  ┌───────────┐              ┌──────────────┐    │
│  │Components │              │  API Client   │    │
│  │ (viz, ui) │              │  + Socket.IO  │    │
│  └───────────┘              └──────┬───────┘    │
└────────────────────────────────────┼────────────┘
                                     │
                    ┌────────────────┼──────────────┐
                    │         Flask Backend          │
                    │  POST /module → task_id        │
                    │  WS: task:state, task:result   │
                    │  GET /apikey, POST /apikey      │
                    └────────────────────────────────┘
```

### Data Flow for a Search

1. User types email/username in search bar → dispatches to `gatherStore`
2. `gatherStore.startSearch(input)` fires POST to each enabled module
3. Each POST returns a `task_id` — stored in `gatherStore.tasks[module]`
4. **WebSocket**: Backend emits `task:state` and `task:result` events per task_id
5. Socket.IO client receives events → updates TanStack Query cache → components re-render
6. **Fallback**: If WS disconnects, TanStack Query falls back to HTTP polling via `/state` and `/result`
7. Results aggregated into `gatherStore.results[module]` with typed shapes
8. Profile/Timeline pages read from the same store, filtered by their view

### State Architecture

| Store | Purpose | Key State |
|-------|---------|-----------|
| `gatherStore` | Search state & results | `input`, `tasks`, `results`, `status` per module |
| `apiKeyStore` | API key management | `keys: ApiKey[]`, CRUD operations |
| `uiStore` | UI preferences | `sidebarOpen`, `theme`, `activeFilters` |

---

## Pages

### Routes

```
/                    → redirect to /gatherer
/gatherer            → Main search + module results (core page)
/profile             → Aggregated profile view
/timeline            → Chronological events
/apikeys             → API key management
```

No `/principal` dashboard — the gatherer IS the landing page.

### Gatherer (core page)

- **Search bar** at top with email/username input + validation
- **Module progress grid**: glanceable status of all running tasks (icons with status badges)
- **Category filter tabs**: All | Social | Leaks | Search | Enrichment
- **Expandable result cards** per module with sub-tabs: Graph | Table | Raw JSON
- **Validation badge** on each card (hard/soft/none)
- **Export** button per module or all at once (JSON)

### Profile

- Avatar, name, email, location header
- Tabs: Overview | Photos | Social | Map
- Aggregates `profile` arrays from all completed modules

### Timeline

- Vertical timeline, newest first
- Aggregates `timeline` arrays from all modules, sorted by date descending
- Icon + text per event

### API Keys

- TanStack Table with inline editing
- Masked key display
- Import/Export JSON buttons
- Add/Edit/Delete operations

---

## Module Registry (Hybrid Component Approach)

```typescript
interface ModuleConfig {
  id: string              // "github", "twitter", etc.
  label: string           // "GitHub"
  icon: IconType
  category: "social" | "email" | "search" | "leak" | "enrichment"
  requiresApiKey?: string
  specialParams?: Record<string, any>
  visualization: {
    useGenericGraph?: boolean
    useGenericChart?: boolean
    useGenericTable?: boolean
    customComponent?: React.FC
  }
}
```

~20 of 28 modules use generic viz components. Custom components only for:
- **Twitter**: Timeline sub-view, popularity metrics
- **GitHub**: Repo grid with language bars
- **Holehe/UserSearch**: Account existence matrix
- **Dorks**: Search result list with source links

---

## Shared Visualization Components

| Component | Library | Used For |
|-----------|---------|----------|
| `ForceGraph` | react-force-graph-2d | Network relationships |
| `ModuleChart` | Recharts | Bar/line/pie charts |
| `DataTable` | TanStack Table | Tabular data |
| `WordCloud` | react-wordcloud | Keyword frequency |
| `LocationMap` | react-leaflet | Geolocation display |
| `ResultCard` | shadcn Card | Expandable module container |
| `StatusBadge` | shadcn Badge | Task status display |
| `ModuleGrid` | CSS Grid | Progress overview |

---

## Dark Hacker Theme

- **Background**: Near-black (`#0a0a0f`) with subtle blue tint
- **Cards**: Dark gray (`#111118`) with faint border glow
- **Accent**: Cyan/teal (`#06b6d4`)
- **Text**: White primary, gray-400 secondary
- **Status colors**: Green (success), amber (pending), red (error), cyan (info)
- **Font**: JetBrains Mono for data, Inter for UI text
- **Effects**: Subtle glow on active elements, scanline-style progress bars

---

## Docker Setup

Coexists alongside old frontend:

```yaml
# docker-compose.yml additions
frontend-next:
  build:
    context: ./frontend-next
    dockerfile: Dockerfile
  ports:
    - "5173:5173"
  depends_on:
    - backend
  environment:
    - VITE_API_URL=http://backend:5000
    - VITE_WS_URL=ws://backend:5000
```

**Dev**: Vite dev server on 5173
**Prod**: Multi-stage build → Nginx serving static files

---

## Backend Changes (Minimal)

1. Add `flask-socketio` to `requirements.txt`
2. Wrap Flask app with `SocketIO(app)`
3. Emit `task:started`, `task:result`, `task:error` events (~15 lines in `api.py`)
4. Update CORS to include `:5173` origin
5. Socket.IO uses Redis as message queue (already available)

No changes to existing HTTP endpoints.

---

## Testing Strategy

| Layer | Tool | Focus |
|-------|------|-------|
| Unit | Vitest | Stores, utilities, data transformers |
| Component | Vitest + Testing Library | Key components with mock data |
| Integration | Playwright | Full page flows |
| API mocking | MSW | Mock backend during dev/tests |

Priority test targets:
- Module registry renders correct viz per module type
- Gather flow: search → task dispatch → result display
- WebSocket connection/reconnection/fallback
- API key CRUD
- Profile/Timeline data aggregation

---

## API Contract Reference

### Standard Module Flow

```
POST /<module> {"username": "target", "from": "Initial"}
→ {"module": "...", "task": "uuid", "param": "...", "from_m": "Initial"}

WS event: task:state {task_id, module, state: "PENDING|SUCCESS|FAILURE"}
WS event: task:result {task_id, module, result: [...]}
```

### Result Shape (array, order-dependent)

```json
[
  {"module": "github"},
  {"param": "target"},
  {"validation": "hard|soft|no|not_used"},
  {"raw": {...}},
  {"graphic": [...]},
  {"profile": [...]},
  {"timeline": [...]},
  {"tasks": [...]}
]
```

### API Keys

- `GET /apikey` → `[{id, name, key}]`
- `POST /apikey` → `[{id, name, key}]` (write)

### 38 Module Endpoints

Social: github, twitter, instagram, tiktok, reddit, tinder, venmo, mastodon, twitch, linkedin, keybase, gitlab, skype, spotify
Email/Leak: emailrep, leaks, leaklookup, darkpass, psbdmp
Username: usersearch, socialscan, sherlock, holehe
Enrichment: peopledatalabs, fullcontact, ghostproject
Search: search, dorks
Special: twitter_info, twitter_infos, twitter_comp, twitter_comps, tweetiment

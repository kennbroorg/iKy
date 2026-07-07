<div align="center" style="margin-bottom: 10px;">
    <img alt="Redis" src="https://img.shields.io/badge/storage-redis-red.svg?style=for-the-badge">
    <img alt="Python" src="https://img.shields.io/badge/python-3.12-informational.svg?style=for-the-badge">
    <img alt="Celery" src="https://img.shields.io/badge/multiprocessing-celery-green.svg?style=for-the-badge">
    <img alt="FastAPI" src="https://img.shields.io/badge/interface-fastapi-009688.svg?style=for-the-badge">
    <img alt="Node" src="https://img.shields.io/badge/node-22.x-brightgreen.svg?style=for-the-badge">
    <img alt="Angular" src="https://img.shields.io/badge/web%20framework-angular%2021-dd0031.svg?style=for-the-badge">
    <img alt="Docker" src="https://img.shields.io/badge/deploy-docker-blue.svg?style=for-the-badge&logo=docker">
</div>

<div align="center">
    <a href="https://gitlab.com/kennbroorg/iKy/blob/iKy/README.es.md">
	<img alt="README Español" src="https://img.shields.io/badge/README-Espa%C3%B1ol-orange.svg?style=for-the-badge">
    </a>
</div>

---

<div align="center">
    <img alt="Logo" src="imgs/Logo-Circular.png">
</div>

---

[Description](#description)&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Installation](#installation)&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Website][website]&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Modules](#modules)&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Issues][issues]&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Supporting](#sponsor)

---

[website]:https://kennbroorg.gitlab.io/ikyweb/
[issues]:https://gitlab.com/kennbroorg/iKy/-/issues/new?issue%5Bassignee_id%5D=&issue%5Bmilestone_id%5D=
[readmees]: README.es.md
[readmeen]: README.md

<h1 align="center">iKy</h1>

<h1 id="description">Description</h1>

iKy is an OSINT tool that collects information from an email address or other selectors and displays the results in a visual interface.

<div align="center">
    <a href="https://vimeo.com/434501702"><img src="imgs/iKySol.gif"></a>
</div>
<div align="center">
    <em>(pending update: reflects the previous frontend)</em>
    <br>
    <a href="https://vimeo.com/434501702">Video Demo</a>
</div>

<h1 id="installation">Installation</h1>

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)
- (Optional) [just](https://github.com/casey/just#installation) task runner

### Quick start

```shell
git clone https://gitlab.com/kennbroorg/iKy.git
cd iKy
just build
just up
```

Open your browser at [http://localhost:4300](http://localhost:4300)

To stop all services:

```shell
just down
```

> `just up` starts `backend`, `iky-frontend`, and `redis`. No other services are launched by default.

### Without Docker (native)

If you cannot run Docker, iKy can run natively: Caddy serves the pre-built
frontend and Redis + Celery + Uvicorn run as local processes. Requires
`redis-server`, Python 3.12, `curl` and `tar` on the host (Caddy is downloaded
automatically).

```shell
just setup          # create the venv
just up-native      # installs deps, downloads Caddy + frontend, starts everything
```

Open your browser at [http://localhost:4300](http://localhost:4300). Stop with Ctrl-C or `just down-native`.

> The frontend is pulled from the latest GitHub release — no Node build needed.
> `tor` is not launched in native mode; only the `darkweb` module needs it.

<h1 id="architecture">Architecture</h1>

| Service | Stack | Port |
|---------|-------|------|
| backend | FastAPI 0.115 + Celery 5.6 | 5000 |
| iky-frontend | Angular 21 + nginx | 4300 |
| redis | Redis 7 | 56379 (host) |
| tor | SOCKS5 proxy (darkweb module) | internal |

<h1 id="modules">Modules</h1>

iKy routes 26 modules through `backend/module_registry.py`:

| Category | Modules |
|----------|---------|
| Social networks | twitter, linkedin, instagram, tiktok, mastodon, twitch, reddit |
| Identity / username | github, gitlab, keybase, sherlock, socialscan, holehe, usersearch, skype |
| Dating / payments | tinder, venmo |
| Music | spotify |
| Reputation / data brokers | peopledatalabs, emailrep, fullcontact |
| Leaks / breaches | leaks, leaklookup, darkweb, hudsonrock |
| Search | search |

<h1 id="api-keys">API Keys</h1>

Once the application is loaded in the browser, enter your API keys in the settings panel. Below is the full table of fields from `backend/factories/apikeys_default.json`:

|   **Module**   | **Status** | **Field in apikey** | **How to obtain** |
| :------------- | :--------: | :------------------ | :----------------- |
| LinkedIn       | :ok: :cookie: | `linkedin_cookies` (or legacy `linkedin_li_at` / `linkedin_JSESSIONID`) | `just cookies-grab linkedin linkedin.com` or `just cookies-import linkedin <file>` |
| Twitter        | :ok: :cookie: | `twitter_cookies` | `just cookies-grab twitter x.com` |
| TikTok         | :ok: :cookie: | `tiktok_cookies` | `just cookies-grab tiktok tiktok.com` |
| PeopleDataLabs | :ok: | `peopledatalabs_key` | :free: **Free** API — [wiki](https://gitlab.com/kennbroorg/iKy/-/wikis/APIs/ApiKeys-get#peopledatalabs) |
| Emailrep       | :ok: | `emailrep_key` | :free: **Free** API — [wiki](https://gitlab.com/kennbroorg/iKy/-/wikis/APIs/ApiKeys-get#emailrep) |
| Leaklookup     | :ok: | `leaklookup_key` | :free: **Free** API — [wiki](https://gitlab.com/kennbroorg/iKy/-/wikis/APIs/ApiKeys-get#leaklookup) |
| Spotify        | :ok: | `spotify_client_id` / `spotify_client_secret` | :free: **Free** API — [wiki](https://gitlab.com/kennbroorg/iKy/-/wikis/APIs/ApiKeys-get#spotify) |
| Twitch         | :ok: | `twitch_client_id` / `twitch_client_secret` | :free: **Free** API — [wiki](https://gitlab.com/kennbroorg/iKy/-/wikis/APIs/ApiKeys-get#twitch) |
| CSE (Google)   | :ok: | `cse_api_key` / `cse_cx` | :free: **Free** API — [wiki](https://gitlab.com/kennbroorg/iKy/-/wikis/APIs/ApiKeys-get#cse) |
| Brave          | :ok: | `brave_key` | :free: **Free** API |
| Instagram      | :warning: | `instagram_user` / `instagram_pass` | Under revision |
| Fullcontact    | :stop_sign: | `fullcontact_api` | Discontinued |
| HaveIBeenPwned | :stop_sign: | `haveibeenpwned_key` | Discontinued |

> APIs marked with :cookie: use browser session cookies; the rest use service tokens.

<h1 id="cookies">Session cookies</h1>

Some modules (LinkedIn, Twitter, TikTok) require session cookies from your browser. Cookies are stored in `backend/cookies/` (mounted in the container as `/app/cookies`) and persist across restarts. There are two ways to load them, both via `just`.

> Cookies are personal session tokens: do not share them or commit them to the repository (`backend/cookies/` is git-ignored).

### Option A: Import a browser export

Export the site cookies with an extension such as Cookie-Editor to a JSON file and import it:

```shell
just cookies-import linkedin ~/Downloads/linkedin_cookies.json
```

### Option B: Extract them automatically from the browser

Extracts cookies directly from your local browser. Close the browser before running (an open browser locks its cookie database):

```shell
# Try all installed browsers (firefox, chrome, brave, edge)
just cookies-grab linkedin linkedin.com

# Or a specific one
just cookies-grab linkedin linkedin.com brave
```

The command reports, browser by browser, what it could read and what it could not, and writes the file only if it finds the cookies the module needs. For example, LinkedIn requires `li_at` and `JSESSIONID`.

| Module | Domain | Required cookies |
| :----- | :------ | :--------------- |
| LinkedIn | linkedin.com | `li_at`, `JSESSIONID` |
| Twitter | x.com | `auth_token`, `ct0` |
| TikTok | tiktok.com | `msToken` |

> Cookies expire periodically (LinkedIn cookies last between 1 and 3 months). When a module stops authenticating, run the command again.

<h1 id="development">Development</h1>

The development workflow uses a **virtualenv for linting/pre-commit hooks** and **Docker (or the native `just up-native` flow) for building and running** the application.

### Setting up the dev environment

Install [just](https://github.com/casey/just#installation), then:

```shell
just setup
source .venv/bin/activate
```

This creates a Python virtualenv with `pre-commit` and `ruff`, and installs the git hooks.

### Common recipes

| Command | Description |
|---------|-------------|
| `just build` | Build Docker images |
| `just up` | Start all services |
| `just down` | Stop all services |
| `just logs` | Follow backend logs (`just logs frontend` for frontend) |
| `just ps` | Show running containers |
| `just shell-backend` | Open a shell in the backend container |
| `just lint` | Run ruff linter and format check |
| `just fmt` | Auto-format Python code |
| `just restart backend` | Restart a specific service |
| `just rebuild` | Stop, rebuild, and start all services |
| `just clean` | Remove containers, volumes, and local images |
| `just up-native` | Start iKy natively (no Docker) |
| `just down-native` | Stop the native services |
| `just up-native-clean` | Wipe native caches (Caddy, frontend, logs) |

<h1 id="update">Update iKy</h1>

Pull the latest changes and rebuild the Docker images:

```shell
git pull
just rebuild
```

To preserve your API keys across updates, use the Export/Import options in the apikeys menu of the graphical interface.

<div align="center">
    <img alt="apis" height="400" src="imgs/iKy-08.png">
</div>
<div align="center">
    <em>(pending update: reflects the previous frontend)</em>
</div>

# Wiki
- [iKy Wiki](https://gitlab.com/kennbroorg/iKy/-/wikis/home)

# Video Demo

<div align="center">
    <a href="https://vimeo.com/434501702"><img alt="iKy demo" src="imgs/iKy-01.png"></a>
    <p>Vimeo</p>
</div>
<div align="center">
    <em>(pending update: reflects the previous frontend)</em>
</div>

<h1 id="sponsor">Support the project</h1>

Whether you use this project, have learned something from it, or just like it, please consider supporting it by buying me a coffee, so I can dedicate more time on open-source projects like this.

<div align="center" style="margin-top: 30px;">
<a href="https://www.buymeacoffee.com/kennbro" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="80" ></a>
</div>

# Disclaimer

Anyone who contributes or contributed to the project, including me, is not responsible for the use of the tool (Neither the legal use nor the illegal use, nor the "other" use).

Keep in mind that this software was initially written for a joke, then for educational purposes (to educate ourselves), and now the goal is to collaborate with the community making quality free software, and while the quality is not excellent (sometimes not even good) we strive to pursue excellence.

Consider that all the information collected is free and available online, the tool only tries to discover, collect and display it.
Many times the tool cannot even achieve its goal of discovery and collection. Please load the necessary APIs before remembering my mother.
If even with the APIs it doesn't show "nice" things that you expect to see, try other e-mails before you remember my mother.
If you still do not see the "nice" things you expect to see, you can create an issue, contact us by e-mail or by any of the RRSS, but keep in mind that my mother is neither the creator nor Contribute to the project.

We do not refund your money if you are not satisfied.
I hope you enjoy using the tool as much as we enjoy doing it. The effort was and is enormous (Time, knowledge, coding, tests, reviews, etc.) but we would do it again.
Do not use the tool if you cannot read the instructions and / or this disclaimer clearly.

By the way, for those who insist on remembering my mother, she died many years ago but I love her as if she were right here.

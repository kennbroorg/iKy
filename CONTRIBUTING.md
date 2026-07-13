##Main Branch
The idea is that the main branch is iKy. All branches converge in iKy branch.
The previous version (Frontend in AngularJS) is in iKy-v1 branch and we left master branch there too.

##Branch names
- *WIP/featurename*   - For Work In Progress, stuff that will not end soon
- *FEAT/featurename*  - For feature that will be added or expanded
- *BUG/bugname*       - For Bug
- *JUNK/junkname*     - For experimental actions
- *ISSUE/issuenumber* - Obvious
- *REF/refname*       - For violent refactoring
- *IMP/improvename*   - For improvements
- *MISC/miscname*     - For anything else (don't abuse)

##Commits names
- *[ADD] message* - For add
- *[MOD] message* - For modify
- *[REM] message* - For remove
- *[REF] message* - For moderate refactoring
- *[HOT] message* - For hot fix in master
- *[FIX] message* - For fix, but it is not HOT and it's throught another branch, not master
- *[MRG] message* - For Merge
- *[DOC] message* - For documentation

Contributions of any kind are welcome!

##Git Hooks (local setup)

This repo ships with three git hooks, but only one is auto-installed by cloning. The
other two live in `.git/hooks/` of the original dev's local clone and are NOT
distributed via git. Each contributor must install them manually after cloning.

### What runs where

| Hook | Source | Auto-installed? |
|------|--------|-----------------|
| `pre-commit` | pre-commit.com, driven by `.pre-commit-config.yaml` | Yes, on `pre-commit install` |
| `commit-msg` | Local script in `.git/hooks/` of the original dev | No, manual copy |
| `pre-push` | Local script in `.git/hooks/` of the original dev | No, manual copy |

### What each hook does

- **`pre-commit`** runs `ruff check --fix`, `ruff format`, file hygiene (trailing
  whitespace, EOF, YAML, large files, merge markers, AST, TOML, private keys) and
  `hadolint` on any Dockerfile (via Docker, threshold = warning).
- **`commit-msg`** enforces the `[TAG] description` format. Valid tags: `ADD`, `DOC`,
  `FIX`, `MOD`, `MRG`, `REF`, `REM`, `UPD`, `UPT`. Subject must include at least a few
  words after the tag. Conventional commits (e.g. `feat(x): ...`) are rejected.
- **`pre-push`** blocks direct pushes to `main`, `master`, and `iKy` (the default
  branch), then hands off to `git lfs pre-push` so LFS objects are uploaded on
  push. Always go through a feature branch and a PR.

### First-time install

```bash
# 1. Standard venv + pre-commit (this also installs the pre-commit hook)
just setup

# 2. Manually install commit-msg and pre-push from the original repo
#    (replace <path> with the path the original dev shares the scripts from,
#     or copy them from their local .git/hooks/)
cp <path>/commit-msg .git/hooks/commit-msg
cp <path>/pre-push .git/hooks/pre-push
chmod +x .git/hooks/commit-msg .git/hooks/pre-push
```

If you only care about `pre-commit` (ruff, hadolint, file hygiene), step 1 is enough
and step 2 is optional. The commit message format and protected-branch guard are the
two pieces you would lose by skipping step 2.

##Large files (Git LFS)

Some binary assets (the demo GIF and large screenshots under `imgs/`) are stored
with [Git LFS](https://git-lfs.com/) so they don't bloat the `.git` history. The
tracked patterns live in `.gitattributes`:

```
imgs/*.gif      filter=lfs diff=lfs merge=lfs -text
imgs/iKy-08.png filter=lfs diff=lfs merge=lfs -text
```

**You must have Git LFS installed before cloning**, otherwise those files arrive
as ~130-byte text pointers instead of the real images.

```bash
# Debian/Ubuntu
sudo apt install git-lfs
# macOS
brew install git-lfs

# Then, once per machine:
git lfs install
```

If you already cloned without LFS, run `git lfs pull` to fetch the real files.
GitHub provides LFS storage and bandwidth on the free tier (1 GB each), which is
plenty for these assets.

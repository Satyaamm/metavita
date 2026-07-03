# Contributing to MetaVita

Thanks for your interest in contributing. This document describes the branching
strategy and the pull-request workflow.

## Branching strategy

MetaVita uses a two-trunk (GitFlow-lite) model:

| Branch | Purpose | Protected |
|---|---|---|
| `main` | Always releasable / production. Only release and hotfix PRs land here. | Yes |
| `develop` | Integration branch. Day-to-day work merges here first. Default branch. | Yes |
| `feature/*` | New work, branched from `develop`. | No |
| `fix/*` | Bug fixes, branched from `develop`. | No |
| `release/*` | Release stabilization, branched from `develop`, merged to `main` + back to `develop`. | No |
| `hotfix/*` | Urgent production fixes, branched from `main`, merged to `main` + back to `develop`. | No |

### Everyday flow

1. Branch from `develop`: `git switch develop && git switch -c feature/<short-name>`.
2. Commit focused changes; keep the branch up to date with `develop`.
3. Open a pull request **into `develop`**.
4. Ensure CI is green and address review feedback.
5. A maintainer reviews and merges (squash preferred).

### Releases

1. `release/x.y.z` from `develop` for final polish.
2. PR `release/*` → `main`, tag `vx.y.z` on `main`.
3. Merge `main` back into `develop` so it never falls behind.

### Hotfixes

1. `hotfix/<name>` from `main`, PR back into `main`, tag.
2. Merge the fix back into `develop`.

## Pull requests

- Protected branches (`main`, `develop`) accept changes **only through pull requests** —
  no direct pushes or force-pushes.
- Every PR requires at least one approving review before it can be merged; external
  contributors can propose PRs but cannot merge.
- Keep PRs small and focused; write a clear description of what and why.
- CI (lint, tests, build) must pass.

## Local development

See [`README.md`](README.md). In short: `./run.sh` brings up the infra, backend, worker,
and web dev server. Backend uses `ruff` for linting and `pytest` for tests; the web app
uses `tsc` and its build/test scripts.

## Commit messages

Write imperative, present-tense summaries (e.g., "Add pgvector reindex command"). Group
related changes into a single commit where practical.

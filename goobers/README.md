# Goobers config for hass-dreo

This directory is the **version-controlled config source** ("workforce as code")
for running [Goobers](https://github.com/Agent-Clubhouse/Goobers) — a
self-hosted agent-workforce platform — against this repo. It is a *repo-relative
config subtree*, the same pattern Goobers itself dogfoods with its `selfhost/`
directory. **No separate repo is required.**

## What lives here vs. what does NOT

Goobers separates **definitions** (desired state — versioned and reviewed) from
**runtime state** (observed execution — inspected, never committed).

**In this directory (checked in):**

```
goobers/
├── instance.yaml.example        # template; copy into the runtime instance
├── manifest.yaml                # kind: Manifest — top-level desired state
└── gaggles/
    └── hass-dreo/
        ├── gaggle.yaml          # kind: Gaggle — targets JeffSteinbok/hass-dreo
        ├── goobers/             # the workforce (kind: Goober + persona)
        │   ├── curator/         # triages issues -> goobers:ready
        │   ├── nominator/       # nominates items into the ready pool
        │   ├── implementer/     # claims a ready issue -> implements -> commits
        │   ├── reviewer/        # reviews PRs, casts merge verdicts
        │   └── docs/            # keeps README/docs current from code churn
        └── workflows/           # kind: Workflow (state machines)
            ├── backlog-curation.yaml
            ├── work-nomination.yaml
            ├── implementation.yaml
            ├── merge-review.yaml
            ├── pr-remediation.yaml
            └── docs-updater.yaml
```

Each `goobers/<name>/` holds a `goober.yaml` (config) + `instructions.md`
(persona). This is the full **V0 workforce**, adapted from Goobers' own
`selfhost/` dogfood config.

**NOT here (runtime state — materialized OUTSIDE the repo, e.g.
`~/goobers-instances/hass-dreo/`):** `instance.yaml`, `config/`, `runs/`,
`workcopies/`, `scheduler/`, `telemetry.db`. The runtime reads these definitions
but never writes them back. Belt-and-suspenders `.gitignore` entries guard
against anyone materializing an instance inside the tree.

## Setup

1. Install the pinned `goobers` binary (see the project's
   [releases guide](https://github.com/Agent-Clubhouse/Goobers/blob/main/docs/guides/releases.md)),
   or build from source (`go build -o bin/goobers ./cmd/goobers`).
2. Scaffold a runtime instance **outside** this repo and point it at this config
   subtree:
   ```sh
   goobers init ~/goobers-instances/hass-dreo
   cp goobers/instance.yaml.example ~/goobers-instances/hass-dreo/instance.yaml
   # set the instance's workflowSource to this repo's ./goobers directory
   ```
3. Provide credentials (never inline): `export GOOBERS_GITHUB_TOKEN=...`
   (repo + issues + pull-requests scope).
4. Materialize, validate, run:
   ```sh
   goobers config materialize ~/goobers-instances/hass-dreo
   goobers validate           ~/goobers-instances/hass-dreo
   goobers up                 ~/goobers-instances/hass-dreo   # daemon (all workflows)
   # or trigger one workflow manually:
   goobers run backlog-curation ~/goobers-instances/hass-dreo
   ```

## The workforce (V0 loop)

Six workflows form the full issue → PR → merge cycle:

| Workflow | Goober | Trigger | Does |
| --- | --- | --- | --- |
| `backlog-curation` | curator | schedule | Triage/label issues; emit `goobers:ready` + `goobers:approved` |
| `work-nomination` | nominator | schedule | Nominate/propose items into the ready pool |
| `implementation` | implementer, reviewer | schedule | Claim a ready issue → implement → local-CI → PR (reviewer gate) |
| `merge-review` | reviewer | schedule | Reviewer verdict + conjunctive auto-merge |
| `pr-remediation` | implementer, reviewer | schedule | Address review findings / CI failures on open PRs |
| `docs-updater` | docs | manual | Keep `README`/`docs` current from code churn |

`docs-updater` is manual by design (`goobers run docs-updater`); the rest fire
on schedule once the daemon is up.

## How work is selected

`implementation` only claims issues labeled **both** `goobers:approved` (trust)
**and** `goobers:ready`. `backlog-curation` is what produces those labels, so
nothing gets implemented until curation approves an issue — and curation itself
is scoped to the gaggle's backlog `labels` (`goobers`). This is a deliberate,
layered opt-in: no issue is touched, and none is implemented, without passing
the trust gate.

## Notes for this repo

- The gaggle's `ciCommand` is `sh -c "ruff check . && pytest"`, mirroring this
  repo's CI gates. Ruff must report 0 errors (see `ruff.toml`, max line 150) and
  pytest must pass before a PR is opened.
- `python@3.13` capability matching is commented out in both `gaggle.yaml` and
  `instance.yaml.example`; enable both once the daemon host advertises it.
- **`merge-review` needs a second GitHub identity** — an author can't approve
  its own PR. Configure a separate review token (`GOOBERS_GITHUB_REVIEW_TOKEN`)
  before relying on auto-merge.
- **Windows is experimental.** The daemon creates `runs`/`workcopies` symlinks,
  which need admin or **Developer Mode** enabled; the `ciCommand` also assumes a
  POSIX `sh` on PATH (use WSL/Git-Bash). Linux/macOS are the supported tiers.

Always run `goobers validate` after editing anything here.

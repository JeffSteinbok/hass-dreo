# Goobers config for hass-dreo

This directory is both the **version-controlled config source** ("workforce as
code") *and* the **instance root** for running
[Goobers](https://github.com/Agent-Clubhouse/Goobers) — a self-hosted
agent-workforce platform — against this repo. The daemon runs in place
(`goobers up goobers`); its runtime state is written here but gitignored.
**No separate repo and no separate instance directory are required.**

## What lives here vs. what does NOT

Goobers separates **definitions** (desired state — versioned and reviewed) from
**runtime state** (observed execution — inspected, never committed). Both sit
in this one directory; only the definitions are tracked.

**Tracked (checked in):**

```
goobers/
├── instance.yaml.example        # template; copy → instance.yaml locally
├── .gitignore                   # ignores the runtime state listed below
├── README.md
└── config/                      # the daemon reads defs straight from here
    ├── manifest.yaml            # kind: Manifest — top-level desired state
    └── gaggles/
        └── hass-dreo/
            ├── gaggle.yaml      # kind: Gaggle — targets JeffSteinbok/hass-dreo
            ├── goobers/         # the workforce (kind: Goober + persona)
            │   ├── curator/     # triages issues -> goobers:ready
            │   ├── nominator/   # nominates items into the ready pool
            │   ├── implementer/ # claims a ready issue -> implements -> commits
            │   ├── reviewer/    # reviews PRs, casts merge verdicts
            │   └── docs/        # keeps README/docs current from code churn
            └── workflows/       # kind: Workflow (state machines)
                ├── backlog-curation.yaml
                ├── work-nomination.yaml
                ├── implementation.yaml
                ├── merge-review.yaml
                ├── pr-remediation.yaml
                └── docs-updater.yaml
```

Each `config/gaggles/hass-dreo/goobers/<name>/` holds a `goober.yaml` (config)
+ `instructions.md` (persona). This is the full **V0 workforce**, adapted from
Goobers' own `selfhost/` dogfood config. Definitions live under `config/`
because that is where the daemon reads them by default (the instance's
`WorkflowSource` is left unset).

**Ignored (runtime state — the daemon materializes these here on `goobers up`,
and `.gitignore` keeps them out of git):** `instance.yaml`, `runs/`,
`workcopies/`, `scheduler/`, `telemetry.db*`. The runtime reads the definitions
under `config/` but never writes them back.

## Setup

Everything runs from `goobers/` as the instance root — no `goobers init`, no
copying config elsewhere.

1. Install the pinned `goobers` binary (see the project's
   [releases guide](https://github.com/Agent-Clubhouse/Goobers/blob/main/docs/guides/releases.md)),
   or build from source (`go build -o bin/goobers ./cmd/goobers`).
2. Create your local `instance.yaml` (gitignored) from the template:
   ```sh
   cp goobers/instance.yaml.example goobers/instance.yaml
   ```
3. Provide credentials (never inline): `export GOOBERS_GITHUB_TOKEN=...`
   (repo + issues + pull-requests scope).
4. Validate and run, pointing every command at this directory:
   ```sh
   goobers validate goobers
   goobers up       goobers   # daemon (all workflows); creates runs/, workcopies/, ...
   # or trigger one workflow manually:
   goobers run backlog-curation goobers
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

Always run `goobers validate goobers` after editing anything here.

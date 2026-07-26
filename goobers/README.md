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
        ├── goobers/
        │   └── coder/
        │       ├── goober.yaml      # kind: Goober — the coder agent
        │       └── instructions.md  # persona + repo conventions
        └── workflows/
            └── implementation.yaml  # kind: Workflow — claim issue -> PR
```

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
   goobers up                 ~/goobers-instances/hass-dreo   # daemon
   # or trigger one run manually:
   goobers run implementation ~/goobers-instances/hass-dreo
   ```

## How work is selected

The `implementation` workflow only claims issues labeled **both**
`goobers:approved` (trust) **and** `goobers:ready`. Nothing runs against your
issue tracker until you apply those labels — a deliberate opt-in.

## Notes for this repo

- The gaggle's `ciCommand` is `sh -c "ruff check . && pytest"`, mirroring this
  repo's CI gates. Ruff must report 0 errors (see `ruff.toml`, max line 150) and
  pytest must pass before a PR is opened.
- `python@3.13` capability matching is commented out in both `gaggle.yaml` and
  `instance.yaml.example`; enable both once the daemon host advertises it.
- This is a **starter** workflow (linear: claim → implement → local-ci → push →
  open-pr). Graduate to the fully gated flagship workflow (reviewer verdict, CI
  poll repass, escalation, merge policy) via `goobers init --guided` or by
  adapting
  [`config-examples`](https://github.com/Agent-Clubhouse/Goobers/tree/main/config-examples).

Always run `goobers validate` after editing anything here.

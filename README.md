# Confidantic

Confidantic is a deterministic configuration system for Devman-managed projects: a Pydantic wrapper around the CUE CLI.

It provides:

- a devenv module contract for configuration environment setup,
- a Pydantic-based Python library for config/data resolution,
- a required CUE workflow for schema formatting and validation.

## Core principles

- **Pydantic-first runtime models**
- **CUE-required schema workflows** (`cue fmt`, `cue vet`)
- **Just-first developer/CI workflows**
- **Deterministic wrapper merge and snapshot behavior**
- **Safe-by-default redaction**

## Devenv contract

The Confidantic module must set:

- `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`
- `CONFIDANTIC_JUSTFILE=<path to include-able Confidantic justfile>`

It must ensure the config root exists on shell entry and must not set `CONFIDANTIC_PROFILE`.

Required tooling on PATH:

- `confidantic`
- `confidantic-cue`
- `cue`
- `jq`

## Config layout

```text
.devman/.config/
  confidantic.toml
  profiles/
    default.toml
    ci.toml
    local.toml
  modules/
    app.toml
    infra.toml
  data/
    users.jsonl
    endpoints.jsonl
```

## Minimal runtime flow

1. Pydantic model(s) define runtime structure
2. export schema to CUE
3. format with `cue fmt`
4. validate data/snapshots with `cue vet`

Profile precedence:

1. explicit API argument
2. external `CONFIDANTIC_PROFILE`
3. `profile_default` in `confidantic.toml`
4. `default`

## Merge semantics

Default behavior:

- dict/object: deep merge
- scalar: replace
- list: replace

Per-field list policy overrides:

- `append`
- `unique`
- `keyed:<field>`

## JSONL policy

- one record type per file
- invalid JSON lines produce warnings with file + line number
- strict mode collects all invalid lines and fails with summary

## CLI (plumbing)

- `confidantic validate`
- `confidantic dump --format json`
- `confidantic env`
- `confidantic fingerprint`

## MVP quickstart commands

In an MVP checkout of this repository:

- The **root** `justfile` is at `./justfile` and currently exposes `just test` only.
- The Confidantic workflow recipes are **not** defined in the root `justfile`.
- Those recipes are provided by `devenv/just/confidantic.just` **when the Confidantic module is integrated** (typically surfaced via `CONFIDANTIC_JUSTFILE`).

If you are in a devenv shell with Confidantic integrated, prioritize CUE-wrapped flows:

- `just -f "$CONFIDANTIC_JUSTFILE" schema:export`
- `just -f "$CONFIDANTIC_JUSTFILE" schema:fmt`
- `just -f "$CONFIDANTIC_JUSTFILE" schema:vet`
- `just -f "$CONFIDANTIC_JUSTFILE" config:validate`
- `just -f "$CONFIDANTIC_JUSTFILE" config:dump`

You can always run the plumbing CLI directly (also CUE-oriented via wrapper-backed workflows):

- `confidantic validate`
- `confidantic dump --format json`

| Goal | Command | Where defined |
| --- | --- | --- |
| Run repository checks in MVP checkout | `just test` | Root `./justfile` |
| Export CUE schema (module-integrated) | `just -f "$CONFIDANTIC_JUSTFILE" schema:export` | `devenv/just/confidantic.just` (when integrated) |
| Format CUE schema (module-integrated) | `just -f "$CONFIDANTIC_JUSTFILE" schema:fmt` | `devenv/just/confidantic.just` (when integrated) |
| Vet schema/data via CUE (module-integrated) | `just -f "$CONFIDANTIC_JUSTFILE" schema:vet` | `devenv/just/confidantic.just` (when integrated) |
| Validate resolved config | `confidantic validate` | `confidantic` CLI |
| Dump resolved config JSON | `confidantic dump --format json` | `confidantic` CLI |

## Required workflow recipes

Confidantic provides an include-able justfile with (provided by `devenv/just/confidantic.just` when module is integrated):

- `schema:export`
- `schema:vet`
- `data:vet`
- `config:validate`
- `config:dump`
- `config:env`
- `config:fingerprint`

## CUE workflow

- export designated schema models to `./build/schemas/cue/`
- run `cue fmt` on generated schemas
- validate resolved snapshots produced by the Python wrapper with `cue vet`
- validate datasets with `cue vet`

`confidantic-cue` is the stable wrapper used by recipes and CI.

## Repository conventions

Recommended structure:

```text
src/confidantic/
  core/
  models/
  cue/
  cue_export/
devenv/
  modules/
  just/
  bin/
tests/
  unit/
  integration/
build/
```

## Quality expectations

Confidantic changes should improve or preserve:

- determinism
- debuggability
- safety/redaction behavior
- module-driven environment contracts
- required CUE workflow behavior

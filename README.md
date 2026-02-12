# Confidantic

Confidantic is a deterministic **Tree-sitter-to-CUE workshop** for Devman-managed projects.

It provides:

- a devenv module contract for environment and workflow setup,
- a Python library for deterministic workshop processing,
- required CUE workflows for formatting and validation,
- just-first command surfaces for humans and agents.

## Why Confidantic

Confidantic focuses on fast iteration for generating CUE schema/files from Tree-sitter artifacts:

- `node-types.json` from Tree-sitter generation/build
- query `.scm` files (highlights/tags and related semantics)
- deterministic CUE synthesis
- required `cue fmt` + `cue vet`
- structured JSONL provenance logs

## Core workshop loop

```bash
# 1) update grammar and query files
# 2) generate/update tree-sitter artifacts
just cue:from-ts:generate <grammar>

# 3) normalize output
just cue:from-ts:fmt <grammar>

# 4) validate schema/data/snapshots
just cue:from-ts:vet <grammar>

# 5) run doctor checks + iterate
just cue:from-ts:doctor <grammar>
```

One-shot loop:

```bash
just cue:from-ts:workshop <grammar>
```

## Required architecture contracts

- **CUE-required workflow:** use `cue fmt` and `cue vet`; no alternate validation path.
- **Deterministic outputs:** stable input discovery, stable generation order, stable serialized snapshots.
- **Safe-by-default output:** redacted logs/snapshots via `to_redacted_dict()` conventions.
- **Just-first workflows:** recipes are primary interface; CLI remains thin plumbing.

## Devenv contract

The Confidantic module must set:

- `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`
- `CONFIDANTIC_JUSTFILE=<path to include-able Confidantic justfile>`

It must ensure the config root exists on shell entry and must not set `CONFIDANTIC_PROFILE`.

Required tooling on PATH:

- `tree-sitter`
- `cue`
- `jq`
- `confidantic`
- `confidantic-cue`

## Key inputs and artifacts

Typical workshop artifacts:

```text
build/
  treesitter/
    <grammar>/
      node-types.json
      queries/
        highlights.scm
        tags.scm
  schemas/
    cue/
      <grammar>/
        *.cue

logs/
  workshop.jsonl
```

## CLI (plumbing)

Required commands:

- `confidantic validate`
- `confidantic dump --format json`
- `confidantic env`
- `confidantic fingerprint`

## Required recipe compatibility

Confidantic must continue to provide:

- `schema:export`
- `schema:vet`
- `data:vet`
- `config:validate`
- `config:dump`
- `config:env`
- `config:fingerprint`

These are expected to map internally to the workshop implementation as needed.

## Recommended workshop recipes

- `cue:from-ts:generate <grammar>`
- `cue:from-ts:fmt <grammar>`
- `cue:from-ts:vet <grammar>`
- `cue:from-ts:test <grammar>`
- `cue:from-ts:doctor <grammar>`
- `cue:from-ts:workshop <grammar>`

## Validation expectations

Confidantic should validate:

- generated CUE schema structure
- snapshot inputs intended for `cue vet`
- dataset records against generated schemas
- workshop input quality (missing/invalid query artifacts, malformed node-types)

## Additional documentation

- [CONFIDANTIC_CONCEPT.md](./CONFIDANTIC_CONCEPT.md) — canonical concept and architecture scope
- [AGENTS.md](./AGENTS.md) — implementation guidance and non-negotiable contracts
- [ROADMAP.md](./ROADMAP.md) — phased implementation roadmap

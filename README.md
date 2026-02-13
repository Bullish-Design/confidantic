# Confidantic

Confidantic is a deterministic **Tree-sitter-to-CUE workshop** for Devman-managed projects.

It provides:

- a devenv module contract for environment and workflow setup,
- a Python library for deterministic workshop processing,
- required CUE workflows for formatting and validation,
- just-first command surfaces for humans and agents.

## Migration notice

Confidantic now exposes grouped CLI commands and workshop-first recipes as the primary interface.

- Existing required compatibility commands/recipes are still supported.
- New adoption and cutover guidance is documented in [docs/MIGRATION.md](./docs/MIGRATION.md).
- CI usage patterns are documented in [docs/CI_INTEGRATION.md](./docs/CI_INTEGRATION.md).

## Why Confidantic

Confidantic focuses on fast iteration for generating CUE schema/files from Tree-sitter artifacts:

- `node-types.json` from Tree-sitter generation/build,
- query `.scm` files (`highlights.scm`, `tags.scm`, and related semantics),
- deterministic CUE synthesis,
- required `cue fmt` + `cue vet`,
- structured JSONL provenance logs.

## Core workshop loop (Just-first)

```bash
# Validate workshop inputs
confidantic workflow doctor <grammar>

# Generate deterministic CUE files from Tree-sitter artifacts
confidantic workflow generate <grammar>

# Format generated CUE files
confidantic workflow fmt <grammar>

# Validate generated outputs
confidantic workflow vet <grammar>
```

One-shot loop:

```bash
confidantic workflow workshop <grammar>
```

## Workshop command examples (CLI)

```bash
# Generate workshop schemas from Tree-sitter inputs
confidantic workshop generate \
  --grammar python \
  --node-types build/treesitter/python/node-types.json \
  --queries-dir build/treesitter/python/queries \
  --output-dir build/schemas/cue/python

# Validate generated workshop outputs
confidantic workshop validate \
  --grammar python \
  --output-dir build/schemas/cue/python

# Diagnose input/output health
confidantic workshop doctor \
  --grammar python \
  --node-types build/treesitter/python/node-types.json \
  --queries-dir build/treesitter/python/queries
```

## Required architecture contracts

- **CUE-required workflow:** use `cue fmt` and `cue vet`; no alternate validation path.
- **Deterministic outputs:** stable input discovery, stable generation order, stable serialized snapshots.
- **Safe-by-default output:** redacted logs/snapshots via `to_redacted_dict()` conventions.
- **Just-first workflows:** recipes are primary interface; CLI remains thin plumbing.

## Devenv contract

The Confidantic module must set:

- `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`

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

## Command reference

### `config` commands

- `confidantic config validate`
- `confidantic config dump --format json`
- `confidantic config env [--export]`
- `confidantic config fingerprint`

### `schema` commands

- `confidantic schema export --grammar <grammar> --node-types <path> --queries-dir <dir> --output-dir <dir>`
- `confidantic schema vet --output-dir <dir> [--grammar <grammar>]`

### `workshop` commands

- `confidantic workshop generate --grammar <grammar> --node-types <path> --queries-dir <dir> --output-dir <dir>`
- `confidantic workshop doctor --grammar <grammar> --node-types <path> --queries-dir <dir> [--schemas-dir <dir>]`
- `confidantic workshop validate --output-dir <dir> [--grammar <grammar>]`

### `logs` commands

- `confidantic logs show [--limit N] [--grammar <grammar>] [--stage <stage>] [--status <status>] [--format text|json|jsonl]`
- `confidantic logs stats [--format text|json|jsonl]`
- `confidantic logs query [filters...] [--format text|json|jsonl]`

### `migrate` commands

- `confidantic migrate check [--path confidantic.toml] [--format json|text]`
- `confidantic migrate apply [--path confidantic.toml] [--backup/--no-backup] [--format json|text]`
- `confidantic migrate doctor [--root .] [--format json|text]`

### Legacy compatibility root commands

- `confidantic validate`
- `confidantic dump --format json`
- `confidantic env [--export]`
- `confidantic fingerprint`

## Workflow commands

Use Python-first workflow commands:

- `confidantic workflow doctor <grammar>`
- `confidantic workflow generate <grammar>`
- `confidantic workflow fmt <grammar>`
- `confidantic workflow vet <grammar>`
- `confidantic workflow workshop <grammar>`
- `confidantic workflow data-vet <grammar> [--data-path <path>]`

## Validation expectations

Confidantic validates:

- generated CUE schema structure
- snapshot inputs intended for `cue vet`
- dataset records against generated schemas
- workshop input quality (missing/invalid query artifacts, malformed node-types)

## Additional documentation

- [CONFIDANTIC_CONCEPT.md](./CONFIDANTIC_CONCEPT.md) — canonical concept and architecture scope
- [AGENTS.md](./AGENTS.md) — implementation guidance and non-negotiable contracts
- [docs/WORKSHOP_LOGS.md](./docs/WORKSHOP_LOGS.md) — workshop provenance JSONL contract
- [docs/MIGRATION.md](./docs/MIGRATION.md) — workflow migration guidance
- [docs/CI_INTEGRATION.md](./docs/CI_INTEGRATION.md) — CI command ordering and templates

# Confidantic Migration Guide

This guide describes how to move from legacy Confidantic usage to the Tree-sitter-to-CUE workshop workflow while preserving existing automation.

## Scope

This migration guide covers:

- old command compatibility and what remains stable,
- recommended workshop-first command surfaces,
- a staged adoption path for local development and CI.

## Compatibility guarantees

Confidantic keeps required legacy entry points available as adapters over the new grouped CLI and workshop recipes.

### Stable CLI compatibility commands

These commands remain available:

- `confidantic validate` (legacy alias of `confidantic config validate`)
- `confidantic dump --format json` (legacy alias of `confidantic config dump --format json`)
- `confidantic env [--export]` (legacy alias of `confidantic config env [--export]`)
- `confidantic fingerprint` (legacy alias of `confidantic config fingerprint`)

### Stable required Just recipes

These recipe names remain available:

- `schema:export`
- `schema:vet`
- `data:vet`
- `config:validate`
- `config:dump`
- `config:env`
- `config:fingerprint`

These adapters delegate to workshop generation/validation and grouped CLI plumbing.

## Old-to-workshop mapping

| Old surface | Workshop-first replacement | Notes |
| --- | --- | --- |
| `just schema:export [grammar]` | `just cue:from-ts:generate <grammar>` + `just cue:from-ts:fmt <grammar>` | Legacy recipe still works; workshop form is explicit. |
| `just schema:vet [grammar]` | `just cue:from-ts:vet <grammar>` | Same validation intent via `confidantic-cue vet`. |
| `confidantic validate` | `confidantic config validate` | Legacy alias preserved. |
| `confidantic dump --format json` | `confidantic config dump --format json` | Legacy alias preserved. |
| `confidantic env --export` | `confidantic config env --export` | Legacy alias preserved. |
| `confidantic fingerprint` | `confidantic config fingerprint` | Legacy alias preserved. |

## Migration prerequisites

1. Ensure devenv exports `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`.
2. Ensure `CONFIDANTIC_ROOT` exists (`mkdir -p "$CONFIDANTIC_ROOT"` on shell entry).
3. Ensure required tooling is available on `PATH`:
   - `tree-sitter`
   - `cue`
   - `jq`
   - `confidantic`
   - `confidantic-cue`
4. Ensure Tree-sitter inputs exist for each grammar:
   - `build/treesitter/<grammar>/node-types.json`
   - `build/treesitter/<grammar>/queries/*.scm`

## Step-by-step adoption

### Step 1: Keep current automation running (no behavior break)

Leave existing calls in place:

```bash
just schema:export
just schema:vet
just config:validate
```

These continue to work through compatibility adapters.

### Step 2: Move scripts to grouped CLI and workshop commands

Adopt grouped commands for clarity:

```bash
confidantic config validate
confidantic config dump --format json
confidantic workshop doctor \
  --grammar <grammar> \
  --node-types build/treesitter/<grammar>/node-types.json \
  --queries-dir build/treesitter/<grammar>/queries
```

### Step 3: Adopt workshop-first Just workflow

Use explicit workshop targets in local iteration and CI:

```bash
just cue:from-ts:doctor <grammar>
just cue:from-ts:generate <grammar>
just cue:from-ts:fmt <grammar>
just cue:from-ts:vet <grammar>
```

Or one-shot:

```bash
just cue:from-ts:workshop <grammar>
```

### Step 4: Add migration diagnostics for config files

Use the `migrate` group to detect and apply known key renames:

```bash
confidantic migrate check --path confidantic.toml --format text
confidantic migrate doctor --root . --format text
confidantic migrate apply --path confidantic.toml --backup --format text
```

Known rewrites:

- `config_root` -> `root`
- `profile` -> `profile_default`
- `data_file` -> `data_files`

### Step 5: Switch CI to workshop-first checks

1. Run doctor checks for required Tree-sitter artifacts.
2. Generate CUE schemas deterministically.
3. Format with `cue fmt` via wrapper/recipes.
4. Validate schemas and data with `cue vet`.
5. Optionally query workshop logs for regression signals.

See [CI integration examples](./CI_INTEGRATION.md) for concrete pipelines.

## Rollback strategy

If workshop-first updates surface integration issues:

1. Continue running stable adapter recipes/aliases (`schema:*`, `config:*`, legacy CLI wrappers).
2. Fix artifact paths and grammar-specific Tree-sitter inputs.
3. Re-enable workshop-first commands incrementally per grammar.

Because compatibility surfaces remain in place, migration can proceed gradually without a forced cutover.

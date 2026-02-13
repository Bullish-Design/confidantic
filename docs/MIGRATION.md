# Confidantic Migration Guide

This guide describes migration from Just-driven workflows to Python-first workflow commands.

## Stable compatibility commands

These root commands remain available:

- `confidantic validate`
- `confidantic dump --format json`
- `confidantic env [--export]`
- `confidantic fingerprint`

## New canonical workflow surface

Use the `workflow` group as the primary interface:

- `confidantic workflow doctor <grammar>`
- `confidantic workflow generate <grammar>`
- `confidantic workflow fmt <grammar>`
- `confidantic workflow vet <grammar>`
- `confidantic workflow workshop <grammar>`
- `confidantic workflow data-vet <grammar> [--data-path <path>]`

## Prerequisites

1. `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`
2. `mkdir -p "$CONFIDANTIC_ROOT"`
3. PATH includes: `tree-sitter`, `cue`, `jq`, `confidantic`, `confidantic-cue`
4. Tree-sitter inputs exist:
   - `build/treesitter/<grammar>/node-types.json`
   - `build/treesitter/<grammar>/queries/*.scm`

## Step-by-step cutover

1. Replace old Just calls with `confidantic workflow ...` commands.
2. Keep `confidantic config ...` for plumbing-level config operations.
3. Keep root aliases only where backward compatibility is needed.
4. Update CI scripts to call workflow commands directly.

## Suggested CI command order

1. `confidantic config validate`
2. `confidantic workflow doctor <grammar>`
3. `confidantic workflow generate <grammar>`
4. `confidantic workflow fmt <grammar>`
5. `confidantic workflow vet <grammar>`
6. optional: `confidantic logs stats --format json`
7. optional: `confidantic migrate doctor --root . --format json`

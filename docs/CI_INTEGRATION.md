# CI Integration

This document provides CI patterns for Confidantic using the current grouped CLI and workshop-first Just recipes.

## CI objectives

A minimal CI pipeline should:

1. verify config plumbing surfaces,
2. run workshop diagnostics against Tree-sitter inputs,
3. generate and format CUE outputs,
4. validate schemas/data with `cue vet`,
5. optionally inspect workshop provenance logs.

## Environment contract in CI

Confidantic expects:

- `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`
- existing directory at `$CONFIDANTIC_ROOT`
- tool availability on `PATH`: `tree-sitter`, `cue`, `jq`, `confidantic`, `confidantic-cue`

Typical bootstrap:

```bash
export CONFIDANTIC_ROOT="$PWD/.devman/.config"
mkdir -p "$CONFIDANTIC_ROOT"
```

## GitHub Actions example

```yaml
name: confidantic

on:
  pull_request:
  push:
    branches: [main]

jobs:
  workshop:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Install your project/dev environment here (devenv, uv, nix, etc.)
      - name: Prepare Confidantic env
        run: |
          export CONFIDANTIC_ROOT="$GITHUB_WORKSPACE/.devman/.config"
          mkdir -p "$CONFIDANTIC_ROOT"
          echo "CONFIDANTIC_ROOT=$CONFIDANTIC_ROOT" >> "$GITHUB_ENV"

      - name: Config plumbing
        run: |
          confidantic config validate
          confidantic config dump --format json
          confidantic config env --export
          confidantic config fingerprint

      - name: Workshop doctor
        run: |
          confidantic workshop doctor \
            --grammar python \
            --node-types build/treesitter/python/node-types.json \
            --queries-dir build/treesitter/python/queries

      - name: Workshop generation + vet (Just)
        run: |
          just --justfile scripts/confidantic.just cue:from-ts:workshop python

      - name: Optional logs query
        run: |
          confidantic logs stats --format json
          confidantic logs show --limit 50 --format text
```

## GitLab CI example

```yaml
stages:
  - validate

confidantic:workshop:
  image: python:3.12
  stage: validate
  script:
    - export CONFIDANTIC_ROOT="$CI_PROJECT_DIR/.devman/.config"
    - mkdir -p "$CONFIDANTIC_ROOT"

    # Install your environment/tooling before running commands.
    - confidantic config validate
    - confidantic workshop doctor --grammar python --node-types build/treesitter/python/node-types.json --queries-dir build/treesitter/python/queries
    - just --justfile scripts/confidantic.just cue:from-ts:generate python
    - just --justfile scripts/confidantic.just cue:from-ts:fmt python
    - just --justfile scripts/confidantic.just cue:from-ts:vet python

    # Optional compatibility checks
    - just --justfile scripts/confidantic.just schema:export python
    - just --justfile scripts/confidantic.just schema:vet python
```

## Makefile integration example

```make
CONFIDANTIC_ROOT ?= $(CURDIR)/.devman/.config
GRAMMAR ?= python

.PHONY: confidantic-bootstrap confidantic-config confidantic-workshop confidantic-logs confidantic-ci

confidantic-bootstrap:
	@mkdir -p "$(CONFIDANTIC_ROOT)"

confidantic-config: confidantic-bootstrap
	@CONFIDANTIC_ROOT="$(CONFIDANTIC_ROOT)" confidantic config validate
	@CONFIDANTIC_ROOT="$(CONFIDANTIC_ROOT)" confidantic config dump --format json

confidantic-workshop: confidantic-bootstrap
	@CONFIDANTIC_ROOT="$(CONFIDANTIC_ROOT)" just --justfile scripts/confidantic.just cue:from-ts:workshop $(GRAMMAR)

confidantic-logs: confidantic-bootstrap
	@CONFIDANTIC_ROOT="$(CONFIDANTIC_ROOT)" confidantic logs stats --format text

confidantic-ci: confidantic-config confidantic-workshop
```

## CLI groups for CI scripting

Current grouped command surfaces:

- `confidantic config ...`
- `confidantic schema ...`
- `confidantic workshop ...`
- `confidantic logs ...`
- `confidantic migrate ...`

Legacy compatibility aliases remain available for `validate`, `dump`, `env`, and `fingerprint` at root level.

## Suggested CI command order

1. `confidantic config validate`
2. `confidantic workshop doctor ...`
3. `just --justfile scripts/confidantic.just cue:from-ts:generate <grammar>`
4. `just --justfile scripts/confidantic.just cue:from-ts:fmt <grammar>`
5. `just --justfile scripts/confidantic.just cue:from-ts:vet <grammar>`
6. optional `confidantic logs stats --format json`
7. optional `confidantic migrate doctor --root . --format json`

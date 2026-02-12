# Confidantic Implementation Guide

This guide describes the target architecture and execution model for Confidantic.

---

## 1) Architecture boundaries

Confidantic consists of:

- devenv integration layer (module + shell/tooling contract)
- Python core (models, loaders, normalization/merge, redaction, snapshot, fingerprint, validation pipeline)
- CUE integration layer (export + vet wrapper)
- Just recipe layer (developer/CI workflows)

The system is designed for deterministic, safe, machine-friendly behavior.

---

## 2) Recommended repository layout

```text
confidantic/
  pyproject.toml
  src/confidantic/
    __init__.py
    cli.py
    core/
      context.py
      loader_toml.py
      loader_jsonl.py
      pipeline.py
      merge.py
      redaction.py
      fingerprint.py
      snapshot.py
      errors.py
    models/
      base.py
      runtime.py
      resolved.py
      metadata.py
    cue_export/
      exporter.py
      naming.py
      emitters.py
    cue/
      wrapper.py
  devenv/
    modules/
      confidantic.nix
    just/
      confidantic.just
    bin/
      confidantic-cue
  tests/
    unit/
    integration/
  build/
```

---

## 3) Core domain contracts

### 3.1 `BaseConfig`

Shared Pydantic base model with:

- explicit model config
- controlled extra behavior
- stable serialization support
- `to_redacted_dict()` helper

### 3.2 `RuntimeConfig`

Loaded from `confidantic.toml`, focused on runtime workflow contracts:

- model export targets for schema generation
- CUE invocation options (flags, wrappers, path conventions)
- validation input/output paths for snapshots and datasets
- policy flags (including JSONL strict mode)

### 3.3 `DevmanContext`

Serializable runtime context for explicit runtime metadata and overrides.

### 3.4 `ResolvedBundle`

Canonical resolved artifact containing:

- metadata (validation target, schema set, fingerprint)
- normalized config snapshot
- normalized dataset payloads
- redacted serialization path

---

## 4) Loaders

### 4.1 TOML loader

Requirements:

- deterministic file loading order
- stable parse/validation errors including file and key path
- Pydantic validation at parse boundary

### 4.2 JSONL loader

Requirements:

- line-by-line parsing
- single record type per file
- warn/skip invalid lines with file + 1-based line number
- strict mode that collects all invalid lines and fails with summary
- Pydantic validation for valid JSON records

---

## 5) Merge engine

Default merge rules:

- dict: deep merge
- scalar: replace
- list: replace

Field metadata can apply list policies:

- `append`
- `unique`
- `keyed:<field>`

Implementation should be pure-function oriented and deterministic.

---

## 6) Validation pipeline

Pipeline flow:

1. load validation input (resolved config snapshot and/or dataset payload)
2. normalize into canonical deterministic shape
3. produce redacted-safe snapshot representation
4. run `cue vet` against exported schemas
5. surface validation results with stable, machine-readable output

---

## 7) Redaction

Redaction should recurse through models, dicts, and lists and mask:

- secret field types
- explicitly redacted fields

Use a single canonical mask token for consistency.

---

## 8) Snapshot and fingerprint

Snapshot requirements:

- deterministic key ordering
- stable serialization shape
- no volatile data unless explicitly modeled
- directly usable as `cue vet` input and golden-test artifact

Fingerprint should be derived from normalized redacted snapshot content.

---

## 9) CLI surface (plumbing only)

Required commands:

- `confidantic validate`
- `confidantic dump --format json`
- `confidantic env` (supports export mode)
- `confidantic fingerprint`

CLI should remain thin and delegate logic to core services.

---

## 10) CUE export and wrapper

### 10.1 Schema export

- discover designated export target models
- export all designated models to `./build/schemas/cue/`
- run `cue fmt` on generated files

A JSON Schema intermediate may be used before CUE emission.

### 10.2 Wrapper

`confidantic-cue` should provide a stable invocation surface for recipes/CI:

- normalize argument conventions
- apply `jq` transforms where schema shape requires it
- call `cue` with consistent flags and paths

---

## 11) Devenv module contract

`devenv/modules/confidantic.nix` should provide:

- `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`
- `CONFIDANTIC_JUSTFILE=<absolute path to devenv/just/confidantic.just>`
- shell hook ensuring `CONFIDANTIC_ROOT` exists
- PATH tooling: `cue`, `jq`, `confidantic`, `confidantic-cue`

Do not set `CONFIDANTIC_PROFILE`.

---

## 12) Required Just recipes

`devenv/just/confidantic.just` should include:

- `schema:export`
- `schema:vet`
- `data:vet`
- `config:validate`
- `config:dump`
- `config:env`
- `config:fingerprint`

Recipes should be composable and CI-friendly.

---

## 13) Testing requirements

Unit coverage:

- merge semantics and all list policies
- JSONL warning behavior and strict-mode aggregated errors
- redaction recursion

Integration coverage:

- deterministic validation pipeline output generation
- stable snapshot serialization
- schema export artifacts and `cue fmt`
- schema vet success/failure paths
- data vet success/failure paths
- devenv environment contract

Golden coverage:

- byte-stable redacted resolved snapshot fixtures

# Confidantic Concept

Confidantic is a deterministic **Tree-sitter-to-CUE workshop** for Devman-managed projects. It combines:

1. an importable **devenv module**,
2. a **Python library** for deterministic artifact processing and generation,
3. a **required CUE workflow** for schema formatting and validation.

---

## 1) Canonical workshop workflow

A developer or agent should be able to:

1. Generate/update Tree-sitter outputs (`node-types.json`) and maintain query `.scm` files.
2. Convert these inputs into deterministic CUE schema/files.
3. Format generated CUE with `cue fmt`.
4. Validate schemas, data, and snapshots with `cue vet`.
5. Iterate quickly with diagnostics and JSONL provenance logs.

Confidantic provides commands and recipes that make this loop standard and repeatable.

---

## 2) Design principles

### 2.1 Tree-sitter artifacts are source inputs for schema generation

Confidantic consumes:

- `node-types.json` from Tree-sitter builds
- query files such as `highlights.scm`, `tags.scm`, and related `.scm` inputs

These inputs drive generated CUE outputs through deterministic transforms.

### 2.2 CUE is required for schema workflows

Confidantic uses CUE for:

- formatting (`cue fmt`)
- validation (`cue vet`)

No non-CUE fallback is part of the architecture.

### 2.3 Just-first, CLI-plumbing architecture

The CLI is intentionally minimal. Most developer and CI interaction should happen through include-able `just` recipes.

### 2.4 Determinism first

Input discovery order, transform order, merge behavior, generated CUE content ordering, and serialized snapshots must be stable and reviewable.

### 2.5 Safety first

Redaction and safe logging are default expectations.

---

## 3) Filesystem and environment contract

### 3.1 Config root

Canonical configuration root:

`<repo_root>/.devman/.config`

The devenv module must export:

- `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`
- `CONFIDANTIC_JUSTFILE=<path to include-able Confidantic justfile>`

The module must ensure the root exists on shell entry.

### 3.2 Profile contract

The module must **not** set `CONFIDANTIC_PROFILE`.

Profile precedence:

1. explicit API argument
2. externally-provided `CONFIDANTIC_PROFILE`
3. `confidantic.toml` `profile_default`
4. `default`

### 3.3 Typical layout

```text
.devman/.config/
  confidantic.toml
  profiles/
    default.toml
    ci.toml
    local.toml
  data/
    *.jsonl

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

---

## 4) Minimal workshop pipeline

Confidantic follows an explicit pipeline:

1. Load Tree-sitter artifacts (`node-types.json`, `.scm` queries).
2. Normalize and validate workshop inputs.
3. Synthesize deterministic CUE schema/files.
4. Format output via `cue fmt`.
5. Validate output/data/snapshots via `cue vet`.
6. Emit structured run logs.

---

## 5) Merge semantics

Default merge behavior:

- dict/object → deep merge
- scalar → replace
- list → replace

Per-field list policies may override default behavior:

- `append`
- `unique`
- `keyed:<field>`

Policies are configured via field metadata and applied deterministically by the Python wrapper.

---

## 6) JSONL policy

- One record type per file.
- Parse line-by-line.
- Invalid JSON lines generate warnings with file + line number.
- Strict mode can collect all errors and fail with a summary.

---

## 7) Redaction and safe output

Confidantic must support redaction across nested structures, including secret types and explicitly marked fields.

`to_redacted_dict()` is the standard safe representation for logs and default CLI output.

---

## 8) Required commands

### 8.1 CLI

- `confidantic validate`
- `confidantic dump --format json`
- `confidantic env`
- `confidantic fingerprint`

### 8.2 Required just recipes

- `schema:export`
- `schema:vet`
- `data:vet`
- `config:validate`
- `config:dump`
- `config:env`
- `config:fingerprint`

These should be implemented in workshop-first form (Tree-sitter input -> CUE generation/validation) while preserving stable names.

### 8.3 Workshop-oriented recipes (recommended)

- `cue:from-ts:generate <grammar>`
- `cue:from-ts:fmt <grammar>`
- `cue:from-ts:vet <grammar>`
- `cue:from-ts:test <grammar>`
- `cue:from-ts:doctor <grammar>`
- `cue:from-ts:workshop <grammar>`

### 8.4 Wrapper

`confidantic-cue` is the stable interface around `cue` (and `jq` shaping where needed).

---

## 9) Export and validation workflow

- Ingest Tree-sitter node types and query semantics.
- Generate CUE schema artifacts to `./build/schemas/cue/`.
- Run `cue fmt` on generated schemas.
- Validate generated schema and snapshots with `cue vet`.
- Validate datasets with `cue vet` against generated record schemas.

All generated artifacts are build outputs.

---

## 10) Definition of done

Confidantic is complete when:

1. devenv contract is fully satisfied (`CONFIDANTIC_ROOT`, `CONFIDANTIC_JUSTFILE`, required PATH tooling, profile behavior).
2. workshop generation from Tree-sitter inputs is deterministic and test-covered.
3. generated CUE outputs are stable and formatted with `cue fmt`.
4. schema/data/snapshot vet paths are operational through wrapper and recipes.
5. CLI remains plumbing-only and delegates business logic to core services.
6. tests cover Tree-sitter input parsing, generation determinism, merge policies, JSONL warnings/strict behavior, redaction, and vet paths.

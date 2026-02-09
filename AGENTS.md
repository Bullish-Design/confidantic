# AGENTS_CONFIDANTIC.md (Confidantic)

This file guides agents implementing **Confidantic**: a devenv.sh importable module plus a Python library with **REQUIRED CUE** for schema export/formatting/validation.

**You MUST read `CONFIDANTIC_CONCEPT.md` first.** That document is the source of truth.

---

## 1) Goals (what “done” looks like)

### 1.1 Devenv module (`confidantic`)
Implement an importable devenv module that:

- always sets `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`
- ensures the directory exists on shell entry
- bundles required tooling on PATH:
  - `cue`
  - `jq`
  - `confidantic` (CLI)
- exposes `CONFIDANTIC_JUSTFILE` pointing at an include-able Confidantic justfile

It must **not** set `CONFIDANTIC_PROFILE`.

### 1.2 Python library (`confidantic`)
Provide a Python package that:

- loads and validates TOML module configs and JSONL datasets
- uses **Pydantic** for schema definition, validation, and defaults
- supports deterministic overlay resolution and merge semantics
- supports redaction (`to_redacted_dict`) and safe logging
- provides a stable “resolved snapshot” output for tooling and validation

### 1.3 Required CUE integration
Implement a first-class, required workflow:

- Export Pydantic models → `.cue` schema files
- Format schemas with `cue fmt`
- Validate:
  - resolved snapshot JSON with `cue vet`
  - data files (e.g. JSONL records) with `cue vet` against record schemas

Provide a stable wrapper:
- `confidantic-cue` (wrapper that calls `cue` and uses `jq` when needed)

### 1.4 CLI (plumbing-only)
Provide a minimal CLI (no runner):

- `confidantic validate`
- `confidantic dump --format json`
- `confidantic env` (emit `KEY=VALUE` lines)
- `confidantic fingerprint`

### 1.5 Just recipes (required)
Ship a justfile include (for consumer repos to import):

- `schema:export`  (Pydantic → CUE + fmt)
- `schema:vet`     (resolved snapshot → cue vet)
- `data:vet`       (datasets → cue vet)
- `config:validate`, `config:dump`, `config:env`, `config:fingerprint`

---

## 2) Non-negotiable contracts

1) **CUE is REQUIRED.** No alternative validation path exists.
2) **`CONFIDANTIC_ROOT` comes from devenv** and is always set.
3) **Profile is not set by devenv.** Env overrides are intentional; defaults come from `confidantic.toml`.
4) **Determinism:** resolution order and merging must be stable.
5) **Safety:** support redaction; do not print secrets by default.
6) **JSONL:** one record type per file; invalid JSON lines skipped with warnings by default.

---

## 3) Suggested implementation breakdown

### 3.1 Core models
- `RegistryConfig` (from `confidantic.toml`)
- `BaseConfig` (shared base class)
- `DevmanContext` (optional runtime context object)
- `ResolvedBundle` (what `dump` returns)

### 3.2 Loading + parsing
- TOML loader:
  - stable error messages (file + key path)
  - strictness follows Pydantic model config (`extra=forbid/ignore`)
- JSONL loader:
  - parse line-by-line
  - invalid JSON line → warning (include line number)
  - valid JSON → Pydantic model instances (record type per file)

### 3.3 Merge engine
Implement merge with defaults:
- dict deep-merge
- scalar replace
- list replace by default

Allow per-field list merge policies via Pydantic Field metadata:
- append
- unique
- keyed merge

### 3.4 “Resolved snapshot” contract
`confidantic dump --format json` must output a normalized JSON snapshot that is stable enough to be a **CUE vet input** and a golden-test artifact.

- stable ordering where relevant
- include enough metadata for debugging (profile, module list, fingerprint), but avoid secrets (redact)

### 3.5 CUE export
Provide `schema:export`:

- locate “export targets” (Pydantic models designated as configuration roots)
- export `.cue` files into `./build/schemas/cue/`
- run `cue fmt` on all outputs

### 3.6 CUE validation
Provide:
- `schema:vet`: `cue vet` resolved snapshot vs schema(s)
- `data:vet`: `cue vet` datasets (possibly per-record) vs schema(s)

Use `confidantic-cue` wrapper to:
- normalize invocation
- apply `jq` transforms when schema expects a specific shape
- ensure consistent flags

### 3.7 Tests
Minimum tests:
- `CONFIDANTIC_ROOT` honored
- profile precedence rules
- deterministic merge behavior (including list policies)
- JSONL warn-skip behavior (stable line numbering)
- redaction behavior (no secrets in dumps)
- schema export produces valid, `cue fmt`-able output
- schema vet succeeds/fails as expected

---

## 4) Acceptance criteria

A change is acceptable if it:
- strengthens determinism, debuggability, and safety
- maintains “Just-first + plumbing-only CLI”
- keeps `CONFIDANTIC_ROOT` module-driven
- keeps CUE required for schema formatting and validation

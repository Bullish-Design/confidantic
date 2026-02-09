# CONFIDANTIC V2 Refactoring Guide (Ground-Up Rewrite)

This guide is for a **clean-break rewrite** of Confidantic aligned to:

- `AGENTS.md` (implementation contracts)
- `CONFIDANTIC_CONCEPT.md` (source of truth for Confidantic)
- `DEVMAN_CORE_CONCEPTS.md` (Devman operating model)

> **No backward compatibility work is needed.**
> Delete legacy assumptions and implement only the new architecture.

---

## 0) Mission and non-negotiables

Before writing code, internalize these hard constraints:

1. **CUE is required** for schema formatting and validation (`cue fmt`, `cue vet`).
2. **devenv module always sets `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`**.
3. **devenv module must not set `CONFIDANTIC_PROFILE`**.
4. **CLI is plumbing only**; `just` is the primary workflow entrypoint.
5. **Determinism and safety are mandatory** (stable merges, redaction by default).
6. **JSONL policy**: one record type per file, invalid lines skipped with warnings by default.

---

## 1) Rewrite strategy (order of execution)

Use this exact order to avoid architecture drift:

1. **Create target project skeleton** (new package layout).
2. **Define core domain models and contracts** (Pydantic-first).
3. **Implement deterministic loaders + resolver + merge engine**.
4. **Implement redaction + stable resolved snapshot output**.
5. **Implement minimal plumbing CLI**.
6. **Implement CUE export + CUE wrapper integration**.
7. **Implement devenv module + Just include recipes**.
8. **Add tests that prove the non-negotiable contracts**.
9. **Remove/replace legacy files and update docs**.

Do not start with CLI or docs first. The data model and resolver contract come first.

---

## 2) Target repository layout (V2)

Refactor to this structure:

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
      resolver.py
      merge.py
      redaction.py
      fingerprint.py
      snapshot.py
      errors.py
    models/
      base.py
      registry.py
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
  build/  # generated artifacts (gitignored)
```

You may adjust filenames slightly, but keep these logical boundaries.

---

## 3) Remove V1 assumptions immediately

Delete or replace legacy behavior that conflicts with V2, including:

- auto-import singleton settings behavior
- recursive `.env` crawling as primary config mechanism
- version-bump-centric CLI behavior
- plugin-mixin runtime mutation patterns for configuration model shape

V2 configuration source is `.devman/.config` with TOML/JSONL + explicit resolution.

---

## 4) Define core Pydantic contracts first

Create these foundational model classes in `src/confidantic/models/`.

### 4.1 `BaseConfig`

Responsibilities:

- common model config defaults
- strict/forbid behavior where needed
- shared helpers:
  - `to_redacted_dict()`
  - stable serialization utility for snapshot generation

Recommended settings:

- explicit `model_config`
- controlled `extra` handling per model (`forbid` by default; override when intentional)

### 4.2 `RegistryConfig` (loaded from `confidantic.toml`)

Should include at least:

- `profile_default: str = "default"`
- module declarations and activation order
- dataset declarations (paths + record model binding)
- policy toggles (optional strict JSONL mode)

### 4.3 `DevmanContext`

Runtime-only context object for injected metadata (e.g. repo path, run metadata, optional jj info).
Keep context explicit and serializable.

### 4.4 `ResolvedBundle`

Canonical resolved output for:

- `confidantic dump --format json`
- `cue vet` input
- golden tests

Include:

- `meta` (profile, module order, fingerprint, generation timestamp policy)
- `config` (resolved merged config)
- `datasets` (validated record payloads)
- redacted view support

---

## 5) Implement loading layer (deterministic and explicit)

### 5.1 TOML loader (`core/loader_toml.py`)

Requirements:

- deterministic load order from registry/module declarations
- stable, user-readable errors with:
  - file path
  - key path
  - expected/actual type details
- Pydantic validation at parse boundary

### 5.2 JSONL loader (`core/loader_jsonl.py`)

Requirements:

- line-by-line parse
- each file bound to one record model type
- invalid JSON line behavior:
  - default: warn + skip
  - warning includes file and 1-based line number
- valid JSON lines validated by Pydantic model

Output should carry both parsed models and warning metadata.

---

## 6) Implement merge semantics engine

Create `core/merge.py` with explicit algorithmic rules:

- dict/object: deep merge
- scalar: replace
- list: replace by default

Then add per-field list policy support via Field metadata:

- `append`
- `unique`
- `keyed:<field>`

Implementation notes for junior dev:

1. Define policy extraction helper from Pydantic field metadata.
2. Keep merge function pure (`left`, `right`, schema info) -> merged value.
3. Normalize dictionary key iteration order.
4. Write focused tests for each list policy and edge case.

---

## 7) Build resolver pipeline

Create `core/resolver.py` with a single orchestrator function/class:

1. resolve profile precedence:
   - explicit API arg
   - `CONFIDANTIC_PROFILE` env override (if set externally)
   - registry `profile_default`
   - fallback `default`
2. load registry
3. load profile overlay
4. load modules in deterministic declared order
5. load datasets
6. apply explicit runtime overrides/context
7. build `ResolvedBundle`
8. compute fingerprint from normalized redacted snapshot

All steps should be observable through structured debug logs (without secrets).

---

## 8) Redaction and safe logging

Implement in `core/redaction.py`:

- mask `SecretStr`, `SecretBytes`
- mask fields marked with redaction metadata
- recurse through nested models/lists/dicts

Define consistent mask token (e.g. `"***REDACTED***"`).

All CLI outputs except explicitly unsafe debug channels should use redacted payloads.

---

## 9) Stable snapshot contract

Implement `core/snapshot.py`:

- deterministic key ordering
- deterministic list ordering where semantics allow
- JSON-safe normalization
- no volatile runtime fields unless intentionally included

`confidantic dump --format json` output must be stable enough for:

- `cue vet` input
- snapshot/golden tests
- predictable fingerprints

---

## 10) CLI (plumbing only)

Implement only these commands in `src/confidantic/cli.py`:

1. `confidantic validate`
2. `confidantic dump --format json`
3. `confidantic env`
4. `confidantic fingerprint`

Behavior guidelines:

- CLI should call resolver/services, not contain business logic.
- Keep output machine-friendly.
- Default to redacted output.
- Non-zero exit codes on validation errors.

---

## 11) CUE export implementation

Create export logic in `src/confidantic/cue_export/`:

1. discover export target models (configuration roots)
2. transform Pydantic model schema to CUE definitions
3. write files into `./build/schemas/cue/`
4. run `cue fmt` on generated outputs

Use stable naming conventions so generated files do not churn unexpectedly.

---

## 12) CUE wrapper (`confidantic-cue`)

Implement `devenv/bin/confidantic-cue` as stable interface over `cue` (+ `jq` when needed):

- normalize argument style across recipes
- apply shape transforms before vet when required
- enforce consistent flags and schema path handling

The goal: recipes and CI call wrapper, not raw `cue` commands with copy-pasted flags.

---

## 13) devenv module implementation

Create `devenv/modules/confidantic.nix` to provide:

- `CONFIDANTIC_ROOT=<repo_root>/.devman/.config` (always)
- `CONFIDANTIC_JUSTFILE=<path-to-confidantic.just>`
- shell hook to `mkdir -p "$CONFIDANTIC_ROOT"`
- packages on PATH:
  - `cue`
  - `jq`
  - `confidantic` CLI
  - `confidantic-cue`

Do **not** set `CONFIDANTIC_PROFILE` here.

---

## 14) required Just recipes

Create include-able justfile at `devenv/just/confidantic.just` with recipes:

- `schema:export`
- `schema:vet`
- `data:vet`
- `config:validate`
- `config:dump`
- `config:env`
- `config:fingerprint`

Recommended behavior:

- `schema:export`: run exporter then `cue fmt`
- `schema:vet`: dump resolved JSON then `confidantic-cue vet ...`
- `data:vet`: vet datasets against record schemas

Recipes should be composable and CI-friendly.

---

## 15) testing plan (must be built with rewrite)

Add tests as the implementation is written, not at the end.

### 15.1 Unit tests

- merge semantics
- list policy behavior (`replace`, `append`, `unique`, `keyed`)
- redaction recursion
- profile precedence resolution
- JSONL warn-skip and line numbering

### 15.2 Integration tests

- resolver builds stable `ResolvedBundle` from realistic fixture tree
- snapshot output determinism across repeated runs
- `schema:export` emits valid CUE files and formatting succeeds
- `schema:vet` success and failure paths
- `data:vet` validates per-record schema behavior
- devenv contract checks for env vars and root creation behavior

### 15.3 Golden tests

Store expected redacted resolved snapshot JSON fixtures and compare byte-for-byte.

---

## 16) implementation checklist (junior developer handoff)

Use this checklist to track work:

- [ ] Create V2 package directory skeleton
- [ ] Replace legacy API surface with V2 model/resolver design
- [ ] Implement `BaseConfig`, `RegistryConfig`, `DevmanContext`, `ResolvedBundle`
- [ ] Implement TOML + JSONL loaders with stable errors/warnings
- [ ] Implement deterministic merge engine + list policies
- [ ] Implement resolver orchestration and profile precedence
- [ ] Implement redaction and safe logging
- [ ] Implement stable snapshot + fingerprint generation
- [ ] Implement minimal plumbing CLI commands
- [ ] Implement Pydantic -> CUE export flow
- [ ] Implement `confidantic-cue` wrapper
- [ ] Implement devenv module (`CONFIDANTIC_ROOT`, `CONFIDANTIC_JUSTFILE`, PATH)
- [ ] Implement required Just recipes
- [ ] Add unit/integration/golden tests
- [ ] Remove obsolete docs and update README to V2 architecture

---

## 17) Definition of done (must all be true)

1. Confidantic can resolve `.devman/.config` config into a deterministic redacted snapshot.
2. `confidantic validate`, `dump`, `env`, and `fingerprint` function as plumbing commands.
3. CUE export and vet workflows run through supported recipes/wrapper.
4. devenv module sets `CONFIDANTIC_ROOT` and never sets `CONFIDANTIC_PROFILE`.
5. Just include file provides all required recipes.
6. Tests cover all non-negotiable contracts from AGENTS + concept docs.

If any item is false, the rewrite is incomplete.

---

## 18) Suggested execution timeline (practical)

- **Day 1–2:** architecture skeleton + core models
- **Day 3–4:** loaders + merge engine + resolver
- **Day 5:** redaction + snapshot + fingerprint
- **Day 6:** CLI + CUE export baseline
- **Day 7:** wrapper + justfile + devenv module
- **Day 8–9:** integration tests + golden fixtures
- **Day 10:** cleanup, docs, acceptance verification

Prioritize correctness and determinism over feature breadth.


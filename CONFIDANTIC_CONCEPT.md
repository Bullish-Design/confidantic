# Confidantic Concept

Confidantic is a deterministic configuration system for Devman-managed projects. It combines:

1. an importable **devenv module**,
2. a **Python library** built on Pydantic, and
3. a **required CUE workflow** for schema formatting and validation.

---

## 1) Canonical workflow

A developer should be able to:

1. Define configuration/data models in Pydantic.
2. Resolve layered config from `.devman/.config` with deterministic behavior.
3. Export model schemas to CUE.
4. Validate snapshots and datasets with CUE.

Confidantic provides the commands and recipes that make this flow standard and repeatable.

---

## 2) Design principles

### 2.1 Pydantic is runtime source-of-truth

Pydantic models define shape, defaults, and validation behavior used by the runtime resolver.

### 2.2 CUE is required for schema workflows

Confidantic uses CUE for:

- formatting (`cue fmt`)
- validation (`cue vet`)

No non-CUE fallback is part of the architecture.

### 2.3 Just-first, CLI-plumbing architecture

The CLI is intentionally minimal. Most developer and CI interaction should happen through include-able `just` recipes.

### 2.4 Determinism first

Resolution order, merge behavior, and serialized snapshots must be stable and reviewable.

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

Profile resolution precedence:

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
  modules/
    app.toml
    infra.toml
  data/
    users.jsonl
    endpoints.jsonl
```

---

## 4) Resolution model

Layering order:

1. registry config (`confidantic.toml`)
2. selected profile overlay
3. module overlays (declared deterministic order)
4. referenced datasets
5. explicit runtime overrides/context

Output is a normalized resolved bundle suitable for tooling, debug, and validation.

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

Policies are configured via field metadata and applied deterministically.

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

### 8.2 MVP quickstart commands

In an MVP checkout of this repository:

- The root `justfile` (`./justfile`) currently exposes `just test` only.
- Confidantic workflow recipes are not expected to exist in the root `justfile`.
- Recipe targets below are provided by `devenv/just/confidantic.just` when the module is integrated (typically surfaced via `CONFIDANTIC_JUSTFILE`).

Prefer CUE-wrapped flows for schema/config tasks:

- `just -f "$CONFIDANTIC_JUSTFILE" schema:export`
- `just -f "$CONFIDANTIC_JUSTFILE" schema:fmt`
- `just -f "$CONFIDANTIC_JUSTFILE" schema:vet`
- `just -f "$CONFIDANTIC_JUSTFILE" config:validate`
- `just -f "$CONFIDANTIC_JUSTFILE" config:dump`

Plumbing CLI remains valid:

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

### 8.3 Just recipes

Required recipe names (provided by `devenv/just/confidantic.just` when module is integrated):

- `schema:export`
- `schema:vet`
- `data:vet`
- `config:validate`
- `config:dump`
- `config:env`
- `config:fingerprint`

### 8.4 Wrapper

`confidantic-cue` is the stable interface around `cue` (and `jq` shaping where needed).

---

## 9) Export and validation workflow

- Export designated schema models to `./build/schemas/cue/`.
- Format schemas with `cue fmt`.
- Validate resolved snapshot JSON with `cue vet`.
- Validate dataset records with `cue vet` against record schemas.

All generated artifacts are build outputs.

---

## 10) Definition of done

Confidantic is complete when:

1. devenv contract is fully satisfied (`CONFIDANTIC_ROOT`, `CONFIDANTIC_JUSTFILE`, required PATH tooling, profile behavior).
2. resolver behavior is deterministic and test-covered.
3. snapshot output is stable and safe by default.
4. CUE export + vet workflows are operational through wrapper and recipes.
5. CLI remains plumbing-only and delegates business logic to core services.
6. tests cover profile precedence, merge policies, JSONL warnings/strict behavior, redaction, and schema/data vet paths.

# Confidantic Concept (devenv.sh module + Python library + REQUIRED CUE)

This repository defines **Confidantic**, a ground-up, non-backwards-compatible configuration system designed to be imported as a **devenv.sh module** and used as a **Python library**, with **CUE REQUIRED** for schema formatting and validation.

> **Read order for agents:** `AGENTS.md` requires you to read this file first.

---

## 1) Workflow (canonical)

### 1.1 Authoring (developer experience)
A developer (building a Devman-managed library/project) does the following to manage their library configuration:

1. **Write Pydantic models** representing configuration needs.
2. **Use those models directly in code** exactly like normal Pydantic models.
3. Use Confidantic’s tooling to **export those models to `.cue` schemas**.
4. Use Confidantic’s CUE tooling to **validate config/data against those schemas**.

### 1.2 Tooling (Confidantic responsibility)
Confidantic provides, via its devenv module:

- the `cue` CLI (**required**)
- additional CLI tools needed for workflows (e.g. `jq`)
- a curated set of **Just recipes / scripts** for:
  - exporting Pydantic models → `.cue`
  - `cue fmt` formatting
  - `cue vet` validation of resolved config snapshots and data files

CUE is not optional, and there are no fallback paths when it is unavailable.

---

## 2) Design tenets

### 2.1 Just-first execution
Confidantic may ship a small CLI, but it is *plumbing*, not a task runner. Typical usage is via `just` recipes that call:

- `confidantic validate`
- `confidantic dump`
- `confidantic env`
- `confidantic fingerprint`

### 2.2 The devenv module always sets `CONFIDANTIC_ROOT`
When the module is imported, shells and tasks must have access to the project’s config directory:

- `CONFIDANTIC_ROOT = <repo_root>/.devman/.config`

Additionally:
- the module should **ensure the directory exists** (e.g., `mkdir -p "$CONFIDANTIC_ROOT"` on shell entry)

### 2.3 Profile selection is config-led, not env-led
The devenv module **does not** set `CONFIDANTIC_PROFILE`.

Profile comes from:
1) explicit API argument (highest precedence)
2) `CONFIDANTIC_PROFILE` if explicitly set by a caller/CI
3) `confidantic.toml` default (`profile_default`)
4) fallback `"default"`

### 2.4 Pydantic is the runtime source-of-truth
Confidantic uses Pydantic models to define schemas, defaults, validation rules, and redaction behavior. Baseclasses are provided that represent the core object/type functionality CUE provides.

### 2.5 CUE is the validation and schema-linting engine
- Confidantic exports `.cue` schemas derived from Pydantic models.
- Confidantic uses CUE for:
  - schema formatting (`cue fmt`)
  - schema + instance validation (`cue vet`)
  - deterministic, reviewable validation behavior

---

## 3) Repository shape (monorepo)

Recommended structure:

```
confidantic/
  pyproject.toml
  src/confidantic/
    core/
    models/
    cli.py
    cue_export/              # Pydantic -> CUE export logic
    ...
  templates/
    devman/
      confidantic_component/ # Devman template payload(s)
  build/                     # generated artifacts (ignored)
```

---

## 4) Filesystem contract

### 4.1 The config root
Within a project/repo using Confidantic, the canonical config root is:

```
<repo_root>/.devman/.config/
```

And the devenv module exports:

- `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`

### 4.2 Registry + layout
A typical layout:

```
.devman/.config/
  confidantic.toml
  profiles/
    default.toml
    ci.toml
    local.toml   # usually gitignored
  modules/
    app.toml
    infra.toml
  data/
    users.jsonl
    endpoints.jsonl
```

---

## 5) Resolution model (layering & precedence)

Confidantic supports predictable layering:

1) `confidantic.toml` registry (policy, activated modules, defaults)
2) selected profile overlay (e.g. `profiles/ci.toml`)
3) module config files (e.g. `modules/app.toml`)
4) data files referenced by modules (e.g. `data/*.jsonl`)
5) explicit API overrides / runtime injections (e.g. DevmanContext)

The system must provide a **normalized, inspectable resolved snapshot**.

---

## 6) Merge semantics (recommended defaults)

Confidantic merges overlays deterministically:

- **dict/object**: deep-merge
- **scalar**: replace
- **list**: replace (default)

Lists can opt into alternative policies **per-field** via Pydantic Field metadata, e.g.:

- `replace` (default)
- `append`
- `unique` (dedupe by value)
- `keyed:<field>` (merge list of objects by a unique key)

---

## 7) JSONL policy (recommended defaults)

- JSONL files represent **one record type per file**
- invalid lines are **skipped with a warning** (line-indexed)
- (optional stricter modes may exist, but CUE remains required either way)

---

## 8) Secrets & redaction

Confidantic supports safe logging:

- encourage `SecretStr` / `SecretBytes` where applicable
- allow field-level redaction flags (e.g., `Field(..., json_schema_extra={"redact": True})`)
- `to_redacted_dict()` masks secrets, including nested models

---

## 9) Devenv module contract (importable module `confidantic`)

When imported, the module provides:

### 9.1 Environment variables
- `CONFIDANTIC_ROOT` (always set)
- `CONFIDANTIC_JUSTFILE` (path to an include-able justfile with Confidantic recipes)
- the module must **not** set `CONFIDANTIC_PROFILE`

### 9.2 Tooling (all required)
- Python env including the `confidantic` package
- `confidantic` CLI on `PATH`
- `cue` on `PATH`
- `jq` on `PATH` (used to shape JSON snapshots and/or per-module exports)

### 9.3 Shell hooks
- ensure `CONFIDANTIC_ROOT` exists
- optionally print a one-line hint if the root is empty (first-time initialization)

---

## 10) Required CUE workflow

### 10.1 Export Pydantic models → `.cue`
Confidantic must provide a script/recipe to export schemas that are built on the Confidantic provided ConfigBase:

- `just schema:export`
  - discovers the project’s Confidantic model entrypoints (implementation-defined)
  - exports `.cue` files to `./build/schemas/cue/`
  - runs `cue fmt` on the output

Notes:
- Export output is a build artifact during normal development.
- The same export step is used later in tag-based releases to publish schema artifacts.

### 10.2 Validate resolved config snapshots with `cue vet`
Confidantic must provide a recipe:

- `just schema:vet`
  1) `confidantic dump --format json` → `./build/resolved.json`
  2) `confidantic-cue vet ./build/resolved.json ./build/schemas/cue/...`

`confidantic-cue` is the stable wrapper that:
- ensures correct CUE module/schema paths
- performs any required `jq` shaping to match schema expectations
- runs the correct `cue` subcommands with consistent flags

### 10.3 Validate JSONL datasets
Confidantic must provide a recipe:

- `just data:vet`
  - validates JSONL records against the corresponding `.cue` schema (record-type specific)
  - continues to follow Confidantic’s JSONL parsing policy (warn/skip invalid JSON lines), but **schema validation is done via CUE**

---

## 11) Tagged releases (future pipeline)

At tagged releases, a CI/CD pipeline may:
- run `schema:export` and `schema:vet`
- publish the exported `.cue` schemas as release artifacts (or on a release branch/tag commit)

This does not change the day-to-day rule: CUE is required for validation and formatting.

---

## 12) What “non-backwards compatible” means here

- this repo/module defines the **canonical** Confidantic behavior going forward
- compatibility shims should live outside the core library unless explicitly required

---

## 13) Related docs

- **Implementation guidance for agents:** `AGENTS.md`
- **Integration skill for other libraries:** `CREATE_CONFIG.md`

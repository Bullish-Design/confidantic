# CREATE_CONFIG.md (Agent Skill): Adopt Confidantic for configuration (CUE REQUIRED)

This is a reusable agent playbook for creating/refactoring configuration to use **Confidantic** with **REQUIRED CUE** for schema export/formatting/validation.

Use it when:
- a repo/library has ad-hoc config parsing (TOML/YAML/env vars/etc.)
- you want standardized validation, layering, debug tooling, and schema-driven enforcement
- you want Devman-friendly config patterns (Just-first, `.devman/.config`, devenv-provided `CONFIDANTIC_ROOT`)

---

## 0) Preconditions (required)

The target repo must import the **confidantic devenv module**, so the environment provides:

- `CONFIDANTIC_ROOT` (always set)
- `cue` (required)
- `jq` (required)
- `confidantic` CLI (required)
- `CONFIDANTIC_JUSTFILE` (a justfile include with Confidantic recipes)

There is no supported workflow without CUE.

---

## 1) Inventory existing configuration

Collect:
- all config files currently used (paths, formats)
- all environment variables read
- any defaults embedded in code
- per-environment overrides (local vs CI vs prodlike)
- structured “data” files (JSONL/CSV/JSON)

Output:
- a list of configuration domains (candidate Confidantic modules)
- a list of sensitive values that must be redacted
- a target profile set (usually `default`, `ci`, optionally `local`)

---

## 2) Define module boundaries

A **module** is a cohesive configuration domain with its own schema, file, and consumer.

Examples:
- `app` (toggles, feature flags)
- `infra` (ports, endpoints)
- `data_sources` (dataset selection)
- `secrets` (references, not raw secrets)

Keep module names stable and short.

---

## 3) Create Pydantic models (schema + defaults)

For each module:
- create a Pydantic model
- encode defaults in the model (not scattered in code)
- choose strictness (`extra="forbid"` by default)

### 3.1 Redaction (required)
For sensitive fields:
- use `SecretStr` / `SecretBytes` where possible
- otherwise add a field-level redaction marker (per Confidantic convention)

Ensure dumps/logs are redacted.

### 3.2 List merge policies (explicit)
Defaults should be safe:
- lists replaced by default

If a field needs different behavior, opt-in via field metadata:
- append / unique / keyed merge

---

## 4) Write config files under `CONFIDANTIC_ROOT`

Within:

```
$CONFIDANTIC_ROOT/
```

Create:

### 4.1 Registry: `confidantic.toml`
- declare `schema_version`
- declare activated modules
- declare `profile_default`

### 4.2 Profiles
Create:
- `profiles/default.toml`
- `profiles/ci.toml`
Optionally:
- `profiles/local.toml` (usually gitignored)

Profiles should be overlays, not full copies.

### 4.3 Module config
One TOML file per module under `modules/`.

### 4.4 Data files
For structured datasets:
- JSONL is “one record type per file”
- invalid JSON lines are skipped with warnings (line-indexed)
- schema validation is performed via CUE

---

## 5) Wire consumers to Confidantic

Replace ad-hoc parsing with Confidantic loads.

Patterns:
- module-level load: `config = load_module("app", AppConfig)`
- bundle load at startup, pass typed config objects down

Avoid rereading config across the codebase.

If Devman run context matters, pass a `DevmanContext` object (or use Confidantic’s context gathering if provided).

---

## 6) Add Just recipes (required)

Import the Confidantic justfile include (via `CONFIDANTIC_JUSTFILE`), or copy the recipes in if your project’s policy forbids includes.

At minimum, ensure these exist:

- `just config:validate` → `confidantic validate`
- `just config:dump` → `confidantic dump --format json`
- `just config:env` → `confidantic env`
- `just config:fingerprint` → `confidantic fingerprint`

Add profile-specific variants by setting `CONFIDANTIC_PROFILE` inline:

- `just config:validate-ci` → `CONFIDANTIC_PROFILE=ci confidantic validate`
- `just config:dump-ci` → `CONFIDANTIC_PROFILE=ci confidantic dump --format json`

Do **not** set `CONFIDANTIC_PROFILE` globally in devenv.

---

## 7) REQUIRED CUE schema workflow

### 7.1 Export schemas (required)
Run:

- `just schema:export`

This exports Pydantic configuration root models to `.cue` schema files and formats them with `cue fmt`.

Outputs should go to:

- `./build/schemas/cue/`

### 7.2 Validate resolved config (required)
Run:

- `just schema:vet`

This:
1) builds a resolved snapshot JSON (via `confidantic dump --format json`)
2) validates it against the generated schemas using `cue vet` (via `confidantic-cue` wrapper)

### 7.3 Validate data files (required)
Run:

- `just data:vet`

This validates datasets (e.g., JSONL records) against record schemas using CUE.

---

## 8) Migration strategy (refactor safely)

Even though Confidantic itself is non-backwards-compatible, you can migrate a target repo incrementally:

1) Add Confidantic models + files
2) Load Confidantic config in parallel with old config
3) Compare resolved values (golden snapshot tests)
4) Switch consumers over
5) Delete old parsing code

If needed, write a one-off script to translate old formats into new TOML/JSONL.

---

## 9) Tests & enforcement (required)

Add tests to enforce:
- config resolution from `CONFIDANTIC_ROOT`
- profile precedence (arg > env > registry > default)
- deterministic merge behavior
- JSONL warn-skip behavior (stable line numbers)
- redaction behavior (no secrets in dumps/logs)
- schema export produces valid `.cue`
- `schema:vet` fails on invalid configurations

Recommended “golden test”:
- run `confidantic dump --format json` (redacted)
- compare to an expected JSON snapshot

---

## 10) Integration checklist (PR-ready)

- [ ] devenv imports the confidantic module
- [ ] `CONFIDANTIC_ROOT` is set and directory exists
- [ ] `.devman/.config/` contains registry + profiles + modules + data
- [ ] Python code uses Confidantic loaders (no ad-hoc parsing remains)
- [ ] Just recipes exist for validate/dump/env/fingerprint (+ ci variants)
- [ ] `just schema:export` works and formats schemas with `cue fmt`
- [ ] `just schema:vet` validates resolved snapshot with `cue vet`
- [ ] `just data:vet` validates datasets with CUE
- [ ] Secrets are redacted in dumps/logs
- [ ] Tests cover precedence + merge + JSONL + redaction + schema vet

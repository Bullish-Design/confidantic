# AGENTS_CONFIDANTIC.md (Confidantic)

This file guides agents implementing **Confidantic** as a devenv.sh importable module plus a Python library with **REQUIRED CUE** for schema export, formatting, and validation.

**You MUST read `CONFIDANTIC_CONCEPT.md` first.** That document is the source of truth.

---

## 1) Mission

Confidantic provides a deterministic configuration system for Devman-managed projects with:

- Pydantic models as runtime source-of-truth
- CUE as required schema/validation engine
- Just-first workflow with a minimal plumbing CLI
- explicit `.devman/.config` filesystem contract
- safe-by-default redaction

---

## 2) Non-negotiable contracts

1. **CUE is REQUIRED.**
   - Use `cue fmt` for schema formatting.
   - Use `cue vet` for validation.
   - No alternate validation path.

2. **`CONFIDANTIC_ROOT` comes from devenv and is always set.**
   - Value: `<repo_root>/.devman/.config`
   - Ensure directory exists on shell entry.

3. **devenv must not set `CONFIDANTIC_PROFILE`.**
   - Profile precedence:
     1) explicit API arg
     2) externally-set `CONFIDANTIC_PROFILE`
     3) `confidantic.toml` `profile_default`
     4) fallback `default`

4. **Determinism is mandatory.**
   - Stable resolution order
   - Stable merge behavior
   - Stable snapshot output for golden tests and CUE vet input

5. **Safety is mandatory.**
   - Redaction support (`to_redacted_dict`)
   - Secrets must not be emitted by default

6. **JSONL contract is mandatory.**
   - One record type per file
   - Parse line-by-line
   - Invalid lines produce warnings with file + line number
   - Strict mode may aggregate errors and fail with summary

---

## 3) Required deliverables

### 3.1 Devenv module (`confidantic`)

Must provide:

- `CONFIDANTIC_ROOT=<repo_root>/.devman/.config`
- `CONFIDANTIC_JUSTFILE=<path-to-confidantic.just>`
- tools on PATH:
  - `cue`
  - `jq`
  - `confidantic` CLI
  - `confidantic-cue` wrapper
- shell hook that runs `mkdir -p "$CONFIDANTIC_ROOT"`

### 3.2 Python package (`confidantic`)

Must provide:

- TOML loader + validation
- JSONL loader + validation
- deterministic resolver and merge engine
- list merge policies:
  - `replace` (default)
  - `append`
  - `unique`
  - `keyed:<field>`
- redaction utilities
- stable normalized resolved snapshot

### 3.3 CUE workflow

Must provide workflow commands for:

- Pydantic model export to `.cue`
- schema formatting via `cue fmt`
- resolved snapshot validation via `cue vet`
- dataset validation via `cue vet`

`confidantic-cue` is the stable wrapper used by recipes and CI.

### 3.4 CLI (plumbing-only)

Required commands:

- `confidantic validate`
- `confidantic dump --format json`
- `confidantic env` (supports export-style output)
- `confidantic fingerprint`

### 3.5 include-able Just recipes

Required recipes:

- `schema:export`
- `schema:vet`
- `data:vet`
- `config:validate`
- `config:dump`
- `config:env`
- `config:fingerprint`

---

## 4) Quality bar

A change is acceptable only if it improves or preserves:

- determinism
- debuggability
- safety
- Just-first ergonomics
- module-driven `CONFIDANTIC_ROOT`
- required CUE validation/formatting workflow

---

## 5) Skills

A skill is a set of local instructions in a `SKILL.md` file. Use only the minimal applicable skills.

### Available skills
- `skill-creator` — create/update Codex skills.
- `skill-installer` — install curated or repo-based skills.

### Skill usage rules
- If user names a skill or request clearly matches one, use it.
- Read only the needed portions of each `SKILL.md`.
- Load only directly relevant references/scripts/assets.
- Prefer script/template reuse over retyping.
- If a skill is missing or blocked, note that briefly and continue with best fallback.

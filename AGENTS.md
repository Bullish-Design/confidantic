# AGENTS_CONFIDANTIC.md (Confidantic)

This file guides agents implementing **Confidantic** as a Tree-sitter-to-CUE workshop module and Python library.

**You MUST read `CONFIDANTIC_CONCEPT.md` first.** That document is the source of truth.

---

## 1) Mission

Confidantic provides a deterministic workshop for generating and validating CUE schemas/files from Tree-sitter artifacts:

- generated `node-types.json`
- query `.scm` files (especially highlights/tags)
- required CUE formatting/validation (`cue fmt`, `cue vet`)
- just-first workflow with minimal plumbing CLI
- explicit `.devman/.config` filesystem contract
- safe-by-default redaction for logs and snapshots

---

## 2) Non-negotiable contracts

1. **CUE is REQUIRED.**
   - Use `cue fmt` for schema formatting.
   - Use `cue vet` for validation.
   - No alternate validation path.

2. **Tree-sitter artifacts are first-class inputs.**
   - `node-types.json` and selected `.scm` query files are required workshop inputs.
   - Workshop generation must be deterministic for identical inputs.

3. **`CONFIDANTIC_ROOT` comes from devenv and is always set.**
   - Value: `<repo_root>/.devman/.config`
   - Ensure directory exists on shell entry.

4. **devenv must not set `CONFIDANTIC_PROFILE`.**
   - Profile precedence:
     1) explicit API arg
     2) externally-set `CONFIDANTIC_PROFILE`
     3) `confidantic.toml` `profile_default`
     4) fallback `default`

5. **Determinism is mandatory.**
   - Stable resolution order
   - Stable merge behavior
   - Stable workshop outputs (generated CUE + snapshots + logs)

6. **Safety is mandatory.**
   - Redaction support (`to_redacted_dict`)
   - Secrets must not be emitted by default

7. **JSONL contract is mandatory.**
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
  - `tree-sitter`
  - `cue`
  - `jq`
  - `confidantic` CLI
  - `confidantic-cue` wrapper
- shell hook that runs `mkdir -p "$CONFIDANTIC_ROOT"`

### 3.2 Python package (`confidantic`)

Must provide:

- deterministic Tree-sitter artifact loaders (`node-types.json`, `.scm` query inputs)
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
- deterministic CUE generation from workshop inputs

### 3.3 CUE workflow

Must provide workflow commands for:

- Tree-sitter artifact -> CUE schema/file generation
- schema formatting via `cue fmt`
- generated schema and snapshot validation via `cue vet`
- dataset validation via `cue vet`

`confidantic-cue` is the stable wrapper used by recipes and CI.

### 3.4 CLI (plumbing-only)

Required commands:

- `confidantic validate`
- `confidantic dump --format json`
- `confidantic env` (supports export-style output)
- `confidantic fingerprint`

Optional workshop plumbing commands may be added, but business logic stays in core services.

### 3.5 include-able Just recipes

Required recipes:

- `schema:export`
- `schema:vet`
- `data:vet`
- `config:validate`
- `config:dump`
- `config:env`
- `config:fingerprint`

Workshop-forward aliases/targets should be added (for example: `cue:from-ts:*`) while preserving required names above.

---

## 4) Quality bar

A change is acceptable only if it improves or preserves:

- determinism
- debuggability
- safety
- Just-first ergonomics
- module-driven `CONFIDANTIC_ROOT`
- required CUE validation/formatting workflow
- Tree-sitter-input-driven generation reliability

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

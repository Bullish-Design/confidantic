# Confidantic Refactoring Proposal: Remove `scripts/confidantic.just` by Folding Workflow Logic into Python

## Executive summary

`scripts/confidantic.just` currently owns most workflow orchestration (path derivation, preflight checks, command composition, compatibility adapters, and CI gate entrypoints). The Python library/CLI already has enough primitives to absorb this behavior, but command responsibilities are split across shell recipes and multiple partially-overlapping modules.

**Proposal:** move workflow orchestration into a first-class Python service + CLI surface, keep only a tiny optional compatibility shim for Just users, and make Python the canonical automation API for local dev and CI.

This removes brittle shell logic, centralizes determinism/safety checks, and improves composability for tools beyond Just.

---

## What is wired to `scripts/confidantic.just` today

## 1) Environment and module contract
- `devenv.nix` exports `CONFIDANTIC_JUSTFILE=${root}/scripts/confidantic.just` and provides wrappers (`confidantic`, `confidantic-cue`).
- README/docs instruct users and CI to call `just --justfile scripts/confidantic.just ...`.
- Integration tests directly reference `scripts/confidantic.just` (`tests/integration/workshop/test_workflow_integration.py`, `tests/integration/workshop/test_python_workshop.py`).

## 2) Responsibilities currently in the Justfile
`scripts/confidantic.just` performs:
- convention-based path resolution (`build/treesitter/<grammar>`, `build/schemas/cue/<grammar>`, `CONFIDANTIC_ROOT`),
- input preflight checks (required files/directories and query existence),
- orchestration of generate → fmt → vet loops,
- legacy compatibility recipes (`schema:*`, `data:*`, `config:*`),
- command routing wrappers (`schema action=...`, `data action=...`, `config action=...`),
- CI wrappers (`ci-test`, `ci-quality`, ...).

## 3) Python-side overlap and gaps
- `src/confidantic/workshop/services.py` already orchestrates load/generate/fmt/vet with logging.
- `src/confidantic/cli/workshop.py` and `src/confidantic/cli/schema.py` expose pieces of this.
- CUE execution logic is duplicated/inconsistent between `src/confidantic/cue/formatter.py` and `src/confidantic/cue/wrapper.py`.
- Path conventions and defaults are not centralized in one Python config object, so Just has become the de-facto workflow engine.

---

## Problems caused by the current split

1. **Two orchestration layers** (Just + Python) means behavior drift risk and duplicated checks.
2. **Shell-heavy control flow** is harder to test than Python service code.
3. **Inconsistent CUE invocation policy** across modules weakens determinism/error handling.
4. **Composability friction** for users who do not want Just (direct CLI/API consumers, CI runners, wrappers).
5. **High doc/test coupling to one file path** (`scripts/confidantic.just`) increases migration cost.

---

## Target architecture (Python-first, composable)

## A) Introduce a workflow orchestration layer in Python
Create `src/confidantic/workflow/` with a small domain API:
- `WorkflowPaths` (resolved canonical paths for root/build/treesitter/schemas/data)
- `WorkflowRunner` (high-level actions: `doctor`, `generate`, `fmt`, `vet`, `workshop`, `data_vet`, `ci_*`)
- `WorkflowPreflight` (all required artifact checks now living in Just)
- `WorkflowResult` models with machine-friendly payloads and stable ordering

This becomes the single source of truth for orchestration.

## B) Add a dedicated CLI command group
Add `confidantic workflow ...` (or `confidantic run ...`) that directly maps to former recipe intent:
- `confidantic workflow doctor --grammar <g>`
- `confidantic workflow generate --grammar <g>`
- `confidantic workflow fmt --grammar <g>`
- `confidantic workflow vet --grammar <g>`
- `confidantic workflow workshop --grammar <g>`
- `confidantic workflow data-vet --grammar <g> [--data-path ...]`

Keep existing `schema/config/workshop` subcommands as compatibility adapters that delegate into the same runner.

## C) Consolidate CUE command execution
Unify CUE execution into a single policy module (prefer `cue/wrapper.py` as canonical; retire duplicated subprocess handling in `cue/formatter.py`).

Goals:
- one error format,
- one cwd/path semantics strategy,
- explicit `cue fmt`/`cue vet` wrappers used everywhere,
- deterministic command argument ordering.

## D) Replace `scripts/confidantic.just` with optional thin shim
Delete heavy logic from `scripts/confidantic.just`.
If Just compatibility is required, keep a minimal include-able shim with one-line delegations only, e.g.:
- `schema:export` -> `confidantic workflow generate+fmt`
- `schema:vet` -> `confidantic workflow vet`
- `data:vet` -> `confidantic workflow data-vet`
- `config:*` -> existing CLI commands

Net result: Just remains optional UX sugar; Python owns behavior.

## E) Centralize path/profile/env resolution
Create a Python config resolver module that encodes:
- `CONFIDANTIC_ROOT` contract,
- grammar/data defaults (`CONFIDANTIC_GRAMMAR`, `CONFIDANTIC_DATA_PATH`) with deterministic precedence,
- canonical build tree layout.

No path derivation in shell recipes.

---

## Additional modularity/composability improvements

1. **Package boundaries by capability**
- `confidantic.workshop` for artifact semantics (load/generate/doctor)
- `confidantic.workflow` for orchestration/runtime contracts
- `confidantic.cue` for CUE process wrappers only
- `confidantic.cli` purely for argument parsing + output

2. **Shared typed result envelopes**
Use dataclasses/pydantic models for all runner outputs; keep one JSON schema for CI integration.

3. **Single diagnostics pipeline**
Route doctor/preflight issues through one diagnostics model so terminal/json/jsonl/markdown exports are all rendering modes, not separate logic paths.

4. **Command alias registry**
Define legacy aliases in one mapping table to avoid manually mirrored wrappers in several places.

5. **CI API stabilization**
Expose a Python callable entrypoint (already partly present via `scripts/ci/phase6_quality_gates.py`) that consumes workflow runner objects instead of shell commands.

---

## Recommended migration plan

## Phase 1: Introduce Python workflow engine (no breakage)
- Build `workflow` package and CLI group.
- Reimplement all current Just orchestration behavior in Python.
- Keep existing commands/recipes delegating to the new layer.

## Phase 2: Unify CUE execution and preflight checks
- Route formatting/validation calls through one CUE wrapper module.
- Remove duplicated subprocess code.
- Ensure deterministic artifact and error ordering.

## Phase 3: Shrink/remove heavy Justfile
- Replace recipe bodies with thin CLI delegations.
- Option A (preferred for simplification): remove `scripts/confidantic.just` entirely and update docs/tests/devenv to Python commands.
- Option B (compatibility): keep a tiny adapter file with no business logic.

## Phase 4: Update module contracts + docs
- If removing file fully, replace `CONFIDANTIC_JUSTFILE` contract with `CONFIDANTIC_WORKFLOW_ENTRYPOINT` (or document as optional legacy export).
- Update README, migration guide, CI docs, and tests to reference canonical Python workflow commands.

## Phase 5: Hardening
- Expand deterministic tests around workflow runner output ordering and identical-input reproducibility.
- Add migration tests ensuring legacy aliases remain stable until sunset.

---

## Risks and mitigations

- **Risk:** Contract drift with required Just recipes.
  - **Mitigation:** Keep minimal generated shim during deprecation window, with recipes delegating into Python.

- **Risk:** CI scripts depend on exact stdout/stderr wording from Just.
  - **Mitigation:** introduce stable JSON output mode for workflow commands and migrate CI to parse JSON.

- **Risk:** Behavior changes in path defaults.
  - **Mitigation:** codify path resolution in one tested resolver with explicit precedence docs.

---

## Definition of done for this refactor

1. No business logic remains in `scripts/confidantic.just` (or file fully removed).
2. All former recipe workflows are executable through `confidantic` CLI subcommands with equivalent behavior.
3. CUE invocation logic exists in one module and is used by all generation/validation paths.
4. Devenv/docs/tests no longer require direct coupling to `scripts/confidantic.just`.
5. Determinism/safety/logging guarantees are preserved with regression coverage.

# Confidantic Roadmap

This roadmap defines phased delivery for the Tree-sitter-to-CUE workshop scope.

## Phase 0 — Scope lock and contracts

- Lock product scope: Confidantic is a Tree-sitter artifact -> CUE schema workshop.
- Confirm required contracts remain intact:
  - `cue fmt` and `cue vet` are mandatory.
  - required recipe names remain available.
  - `CONFIDANTIC_ROOT` / `CONFIDANTIC_JUSTFILE` devenv contract remains unchanged.
- Publish capture/query conventions to avoid ambiguous `.scm` semantics.
- Define deterministic ordering and naming rules for generated CUE assets.

## Phase 1 — Workshop input model and ingestion

- Add typed models for:
  - Tree-sitter `node-types.json` structure
  - parsed query capture semantics from `.scm` files
  - normalized intermediate representation (IR) used by generators
- Implement deterministic loaders:
  - stable file discovery order
  - strict parse errors with source file + line context
- Add JSONL workshop event model for append-only logs.

Deliverables:
- `src/confidantic/workshop/models.py`
- `src/confidantic/workshop/loaders.py`
- tests for malformed/partial/missing input cases

## Phase 2 — Deterministic CUE generation engine

- Implement synthesis engine from normalized IR to CUE definitions.
- Guarantee stable output:
  - sorted node/capture/field traversal
  - deterministic file segmentation and naming
  - stable emitted blocks/comments
- Include source provenance comments in generated CUE where practical.
- Ensure generation works as build output only (no in-place source mutation).

Deliverables:
- `src/confidantic/workshop/generator.py`
- output under `build/schemas/cue/<grammar>/`
- golden tests for deterministic output

## Phase 3 — Required CUE workflow integration

- Integrate generator output with `confidantic-cue` wrapper flows.
- Add or update just targets:
  - `cue:from-ts:generate`
  - `cue:from-ts:fmt`
  - `cue:from-ts:vet`
  - `cue:from-ts:test`
  - `cue:from-ts:doctor`
  - `cue:from-ts:workshop`
- Preserve required compatibility targets:
  - `schema:export`, `schema:vet`, `data:vet`
  - `config:validate`, `config:dump`, `config:env`, `config:fingerprint`

Deliverables:
- `scripts/confidantic.just` updates
- `src/confidantic/cue/wrapper.py` updates as needed
- integration tests for fmt/vet pass/fail paths

## Phase 4 — Doctoring, diagnostics, and provenance

- Add workshop diagnostics:
  - missing artifact checks (`node-types.json`, required query files)
  - unknown/unmapped captures
  - orphaned node references
  - deterministic diff warnings
- Emit append-only JSONL logs per run:
  - stage (load/generate/fmt/vet/test/doctor)
  - success/failure
  - timing and artifact paths
  - optional agent/session metadata

Deliverables:
- `src/confidantic/workshop/doctor.py`
- `src/confidantic/workshop/logging.py`
- `logs/workshop.jsonl` contract docs and tests

## Phase 5 — CLI plumbing and migration compatibility

- Keep CLI plumbing-only.
- Add optional workshop plumbing subcommands if needed for CI scripting.
- Ensure old command expectations continue to function through adapters.
- Document migration from old Pydantic-export framing to workshop framing.

Deliverables:
- CLI integration updates in `src/confidantic/cli.py`
- migration notes in docs
- command compatibility tests

## Phase 6 — Hardening and quality gates

- Add CI checks for:
  - deterministic generation (golden snapshots)
  - required CUE formatting and vet
  - strict JSONL behavior
  - redaction defaults
- Add end-to-end workshop fixture(s) for at least one grammar.
- Add performance sanity checks for medium-size node-types/query sets.

Deliverables:
- CI recipe updates
- integration fixture suite in `tests/integration/workshop/`
- release readiness checklist

## Definition of roadmap completion

Roadmap is complete when:

1. Tree-sitter artifacts reliably produce deterministic CUE outputs.
2. Required CUE workflows (`cue fmt`, `cue vet`) are first-class and enforced.
3. Required recipe/CLI contracts remain available.
4. Workshop diagnostics and JSONL provenance are stable and useful.
5. Documentation, migration notes, and tests fully reflect the new scope.

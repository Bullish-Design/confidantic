set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

invocation_dir := invocation_directory()
confidantic_root := env_var_or_default("CONFIDANTIC_ROOT", invocation_dir + "/.devman/.config")
compat_grammar := env_var_or_default("CONFIDANTIC_GRAMMAR", "default")
compat_data_path := env_var_or_default("CONFIDANTIC_DATA_PATH", confidantic_root + "/data")
build_dir := invocation_dir + "/build"
schemas_dir := build_dir + "/schemas/cue"
treesitter_dir := build_dir + "/treesitter"

cue-from-ts-generate grammar:
    @node_types="{{treesitter_dir}}/{{grammar}}/node-types.json"; \
    queries_dir="{{treesitter_dir}}/{{grammar}}/queries"; \
    output_dir="{{schemas_dir}}/{{grammar}}"; \
    if [[ ! -f "$node_types" ]]; then \
      echo "error: missing required Tree-sitter artifact: $node_types" >&2; \
      exit 1; \
    fi; \
    if [[ ! -d "$queries_dir" ]]; then \
      echo "error: missing required query directory: $queries_dir" >&2; \
      exit 1; \
    fi; \
    if ! compgen -G "$queries_dir/*.scm" >/dev/null; then \
      echo "error: no .scm query files found in: $queries_dir" >&2; \
      exit 1; \
    fi; \
    mkdir -p "$output_dir" "{{confidantic_root}}"; \
    confidantic workshop generate \
      --grammar "{{grammar}}" \
      --node-types "$node_types" \
      --queries-dir "$queries_dir" \
      --output-dir "$output_dir"

cue-from-ts-fmt grammar:
    @output_dir="{{schemas_dir}}/{{grammar}}"; \
    if [[ ! -d "$output_dir" ]]; then \
      echo "error: missing generated schema directory: $output_dir" >&2; \
      echo "hint: run 'just cue-from-ts-generate {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    if ! compgen -G "$output_dir/*.cue" >/dev/null; then \
      echo "error: no generated CUE files found in: $output_dir" >&2; \
      echo "hint: run 'just cue-from-ts-generate {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    confidantic-cue fmt "$output_dir"

cue-from-ts-vet grammar:
    @output_dir="{{schemas_dir}}/{{grammar}}"; \
    if [[ ! -d "$output_dir" ]]; then \
      echo "error: missing generated schema directory: $output_dir" >&2; \
      echo "hint: run 'just cue-from-ts-generate {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    if ! compgen -G "$output_dir/*.cue" >/dev/null; then \
      echo "error: no generated CUE files found in: $output_dir" >&2; \
      echo "hint: run 'just cue-from-ts-generate {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    confidantic-cue vet "$output_dir"

cue-from-ts-test grammar:
    @just --justfile {{justfile()}} cue-from-ts-generate "{{grammar}}"; \
    just --justfile {{justfile()}} cue-from-ts-fmt "{{grammar}}"; \
    just --justfile {{justfile()}} cue-from-ts-vet "{{grammar}}"

cue-from-ts-doctor grammar:
    @node_types="{{treesitter_dir}}/{{grammar}}/node-types.json"; \
    queries_dir="{{treesitter_dir}}/{{grammar}}/queries"; \
    if [[ ! -f "$node_types" ]]; then \
      echo "error: missing required Tree-sitter artifact: $node_types" >&2; \
      exit 1; \
    fi; \
    if [[ ! -d "$queries_dir" ]]; then \
      echo "error: missing required query directory: $queries_dir" >&2; \
      exit 1; \
    fi; \
    confidantic workshop doctor \
      --grammar "{{grammar}}" \
      --node-types "$node_types" \
      --queries-dir "$queries_dir"

cue-from-ts-workshop grammar:
    @just --justfile {{justfile()}} cue-from-ts-doctor "{{grammar}}"; \
    just --justfile {{justfile()}} cue-from-ts-test "{{grammar}}"

cue-from-ts-clean grammar:
    @output_dir="{{schemas_dir}}/{{grammar}}"; \
    rm -rf "$output_dir"; \
    echo "cleaned $output_dir"

# ---------------------------------------------------------------------------
# Backward-compatible adapters (stable names required by contract)
# ---------------------------------------------------------------------------
#
# Adapter behavior:
# - Stable names remain available for existing automation.
# - Recipes default to CONFIDANTIC_GRAMMAR=default when grammar is not passed.
# - Internal paths follow Phase 3 workshop conventions:
#   - Tree-sitter inputs: build/treesitter/<grammar>/
#   - CUE outputs: build/schemas/cue/<grammar>/

schema-export:
    @just --justfile {{justfile()}} cue-from-ts-generate "{{compat_grammar}}"; \
    just --justfile {{justfile()}} cue-from-ts-fmt "{{compat_grammar}}"

schema-export-grammar grammar:
    @just --justfile {{justfile()}} cue-from-ts-generate "{{grammar}}"; \
    just --justfile {{justfile()}} cue-from-ts-fmt "{{grammar}}"

schema-vet:
    @just --justfile {{justfile()}} cue-from-ts-vet "{{compat_grammar}}"

schema-vet-grammar grammar:
    @just --justfile {{justfile()}} cue-from-ts-vet "{{grammar}}"

data-vet:
    @schema_dir="{{schemas_dir}}/{{compat_grammar}}"; \
    data_path="{{compat_data_path}}"; \
    if [[ ! -d "$schema_dir" ]]; then \
      echo "error: missing generated schema directory: $schema_dir" >&2; \
      echo "hint: run 'just schema-export' first" >&2; \
      exit 1; \
    fi; \
    if [[ ! -e "$data_path" ]]; then \
      echo "error: missing dataset path for validation: $data_path" >&2; \
      echo "hint: set CONFIDANTIC_DATA_PATH or use 'just data-vet-path <path>'" >&2; \
      exit 1; \
    fi; \
    confidantic-cue vet "$data_path" "$schema_dir"

data-vet-grammar grammar:
    @schema_dir="{{schemas_dir}}/{{grammar}}"; \
    data_path="{{compat_data_path}}"; \
    if [[ ! -d "$schema_dir" ]]; then \
      echo "error: missing generated schema directory: $schema_dir" >&2; \
      echo "hint: run 'just schema-export-grammar {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    if [[ ! -e "$data_path" ]]; then \
      echo "error: missing dataset path for validation: $data_path" >&2; \
      echo "hint: set CONFIDANTIC_DATA_PATH or use 'just data-vet-grammar-path {{grammar}} <path>'" >&2; \
      exit 1; \
    fi; \
    confidantic-cue vet "$data_path" "$schema_dir"

data-vet-path data_path:
    @schema_dir="{{schemas_dir}}/{{compat_grammar}}"; \
    if [[ ! -d "$schema_dir" ]]; then \
      echo "error: missing generated schema directory: $schema_dir" >&2; \
      echo "hint: run 'just schema-export' first" >&2; \
      exit 1; \
    fi; \
    if [[ ! -e "{{data_path}}" ]]; then \
      echo "error: missing dataset path for validation: {{data_path}}" >&2; \
      exit 1; \
    fi; \
    confidantic-cue vet "{{data_path}}" "$schema_dir"

data-vet-grammar-path grammar data_path:
    @schema_dir="{{schemas_dir}}/{{grammar}}"; \
    if [[ ! -d "$schema_dir" ]]; then \
      echo "error: missing generated schema directory: $schema_dir" >&2; \
      echo "hint: run 'just schema-export-grammar {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    if [[ ! -e "{{data_path}}" ]]; then \
      echo "error: missing dataset path for validation: {{data_path}}" >&2; \
      exit 1; \
    fi; \
    confidantic-cue vet "{{data_path}}" "$schema_dir"

config-validate:
    @confidantic validate

config-dump:
    @confidantic dump --format json

config-env:
    @confidantic env --export

config-fingerprint:
    @confidantic fingerprint

# Group wrappers that preserve contract semantics in Just-compatible form.
# Usage examples:
#   just schema export
#   just schema export default
#   just schema vet my-grammar
schema action="export" grammar="":
    @selected_grammar="{{if grammar == "" { compat_grammar } else { grammar }}}"; \
    case "{{action}}" in \
      export) \
        if [[ "{{grammar}}" == "" ]]; then \
          just --justfile {{justfile()}} schema-export; \
        else \
          just --justfile {{justfile()}} schema-export-grammar "$selected_grammar"; \
        fi ;; \
      vet) \
        if [[ "{{grammar}}" == "" ]]; then \
          just --justfile {{justfile()}} schema-vet; \
        else \
          just --justfile {{justfile()}} schema-vet-grammar "$selected_grammar"; \
        fi ;; \
      *) \
        echo "error: unsupported schema action '{{action}}' (expected export|vet)" >&2; \
        exit 1 ;; \
    esac

# Usage examples:
#   just data vet
#   just data vet my-grammar
#   just data vet my-grammar path/to/data.jsonl
data action="vet" grammar="" data_path="":
    @selected_grammar="{{if grammar == "" { compat_grammar } else { grammar }}}"; \
    case "{{action}}" in \
      vet) \
        if [[ "{{grammar}}" == "" && "{{data_path}}" == "" ]]; then \
          just --justfile {{justfile()}} data-vet; \
        elif [[ "{{grammar}}" == "" ]]; then \
          just --justfile {{justfile()}} data-vet-path "{{data_path}}"; \
        elif [[ "{{data_path}}" == "" ]]; then \
          just --justfile {{justfile()}} data-vet-grammar "$selected_grammar"; \
        else \
          just --justfile {{justfile()}} data-vet-grammar-path "$selected_grammar" "{{data_path}}"; \
        fi ;; \
      *) \
        echo "error: unsupported data action '{{action}}' (expected vet)" >&2; \
        exit 1 ;; \
    esac

# Usage examples:
#   just config validate
#   just config dump
config action="validate":
    @case "{{action}}" in \
      validate) just --justfile {{justfile()}} config-validate ;; \
      dump) just --justfile {{justfile()}} config-dump ;; \
      env) just --justfile {{justfile()}} config-env ;; \
      fingerprint) just --justfile {{justfile()}} config-fingerprint ;; \
      *) \
        echo "error: unsupported config action '{{action}}' (expected validate|dump|env|fingerprint)" >&2; \
        exit 1 ;; \
    esac

# ---------------------------------------------------------------------------
# Phase 6 quality gates (CI/CD equivalent via Python runner)
# ---------------------------------------------------------------------------

ci-test:
    @python scripts/ci/phase6_quality_gates.py test

ci-quality:
    @python scripts/ci/phase6_quality_gates.py quality

ci-performance:
    @python scripts/ci/phase6_quality_gates.py performance

ci-e2e:
    @python scripts/ci/phase6_quality_gates.py e2e

ci-check: ci-test ci-quality ci-performance

ci-all: ci-check ci-e2e
    @echo "✓ All CI checks passed"

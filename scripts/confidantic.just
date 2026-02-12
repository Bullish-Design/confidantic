set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

confidantic_root := env_var_or_default("CONFIDANTIC_ROOT", ".devman/.config")
compat_grammar := env_var_or_default("CONFIDANTIC_GRAMMAR", "default")
compat_data_path := env_var_or_default("CONFIDANTIC_DATA_PATH", confidantic_root + "/data")
build_dir := "build"
schemas_dir := build_dir + "/schemas/cue"
treesitter_dir := build_dir + "/treesitter"

cue:from-ts:generate grammar:
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

cue:from-ts:fmt grammar:
    @output_dir="{{schemas_dir}}/{{grammar}}"; \
    if [[ ! -d "$output_dir" ]]; then \
      echo "error: missing generated schema directory: $output_dir" >&2; \
      echo "hint: run 'just cue:from-ts:generate {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    if ! compgen -G "$output_dir/*.cue" >/dev/null; then \
      echo "error: no generated CUE files found in: $output_dir" >&2; \
      echo "hint: run 'just cue:from-ts:generate {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    confidantic-cue fmt "$output_dir"

cue:from-ts:vet grammar:
    @output_dir="{{schemas_dir}}/{{grammar}}"; \
    if [[ ! -d "$output_dir" ]]; then \
      echo "error: missing generated schema directory: $output_dir" >&2; \
      echo "hint: run 'just cue:from-ts:generate {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    if ! compgen -G "$output_dir/*.cue" >/dev/null; then \
      echo "error: no generated CUE files found in: $output_dir" >&2; \
      echo "hint: run 'just cue:from-ts:generate {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    confidantic-cue vet "$output_dir"

cue:from-ts:test grammar:
    @just --justfile {{justfile()}} cue:from-ts:generate "{{grammar}}"; \
    just --justfile {{justfile()}} cue:from-ts:fmt "{{grammar}}"; \
    just --justfile {{justfile()}} cue:from-ts:vet "{{grammar}}"

cue:from-ts:doctor grammar:
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

cue:from-ts:workshop grammar:
    @just --justfile {{justfile()}} cue:from-ts:doctor "{{grammar}}"; \
    just --justfile {{justfile()}} cue:from-ts:test "{{grammar}}"

cue:from-ts:clean grammar:
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

schema:export grammar=compat_grammar:
    @just --justfile {{justfile()}} cue:from-ts:generate "{{grammar}}"; \
    just --justfile {{justfile()}} cue:from-ts:fmt "{{grammar}}"

schema:vet grammar=compat_grammar:
    @just --justfile {{justfile()}} cue:from-ts:vet "{{grammar}}"

data:vet grammar=compat_grammar data_path=compat_data_path:
    @schema_dir="{{schemas_dir}}/{{grammar}}"; \
    if [[ ! -d "$schema_dir" ]]; then \
      echo "error: missing generated schema directory: $schema_dir" >&2; \
      echo "hint: run 'just schema:export {{grammar}}' first" >&2; \
      exit 1; \
    fi; \
    if [[ ! -e "{{data_path}}" ]]; then \
      echo "error: missing dataset path for validation: {{data_path}}" >&2; \
      echo "hint: set CONFIDANTIC_DATA_PATH or pass data_path=<path>" >&2; \
      exit 1; \
    fi; \
    confidantic-cue vet "{{data_path}}" "$schema_dir"

config:validate:
    @confidantic validate

config:dump:
    @confidantic dump --format json

config:env:
    @confidantic env --export

config:fingerprint:
    @confidantic fingerprint

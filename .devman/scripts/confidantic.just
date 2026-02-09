# Confidantic Just recipes — include-able justfile for consumer repos.
#
# Include in your project Justfile with:
#   import? "confidantic.just"
#
# Requires:
#   CONFIDANTIC_ROOT — set by devenv module
#   confidantic     — CLI on PATH
#   confidantic-cue — wrapper on PATH
#   cue             — CUE CLI on PATH

# Default build output directory
build_dir := justfile_directory() / "build"
schema_dir := build_dir / "schemas" / "cue"
resolved_json := build_dir / "resolved.json"

# --- Schema recipes ---

# Export Pydantic models to CUE schema files and format them
[group('schema')]
schema-export:
    @mkdir -p "{{schema_dir}}"
    confidantic export-schemas --output-dir "{{schema_dir}}"
    @echo "Schemas exported to {{schema_dir}}"

# Validate resolved config snapshot against CUE schemas
[group('schema')]
schema-vet: schema-export
    @mkdir -p "{{build_dir}}"
    confidantic dump --format json > "{{resolved_json}}"
    confidantic-cue vet "{{resolved_json}}" "{{schema_dir}}"/*.cue
    @echo "Schema vet passed"

# --- Data recipes ---

# Validate JSONL datasets against record CUE schemas
[group('data')]
data-vet: schema-export
    @echo "Validating datasets..."
    @for f in "$CONFIDANTIC_ROOT"/data/*.jsonl; do \
        [ -f "$f" ] || continue; \
        name="$(basename "$f" .jsonl)"; \
        echo "  Validating dataset: $name"; \
        confidantic-cue vet-jsonl "$f" "{{schema_dir}}"/*.cue || exit 1; \
    done
    @echo "Data vet passed"

# --- Config recipes ---

# Validate configuration (load, merge, check for errors)
[group('config')]
config-validate:
    confidantic validate

# Dump resolved configuration as JSON
[group('config')]
config-dump:
    confidantic dump --format json

# Emit resolved configuration as KEY=VALUE lines
[group('config')]
config-env:
    confidantic env

# Print the configuration fingerprint
[group('config')]
config-fingerprint:
    confidantic fingerprint

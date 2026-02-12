# Phase 3: Required CUE Workflow Integration

## Overview

Phase 3 integrates the CUE generation engine (Phase 2) with the Just-first workflow architecture. This phase establishes the primary developer interface through Just recipes and ensures compatibility with existing required targets.

**Goal**: Provide a seamless, Just-first workflow for Tree-sitter-to-CUE generation with mandatory `cue fmt` and `cue vet` integration.

## Prerequisites

- Phase 1 complete (models and loaders)
- Phase 2 complete (generator and formatter)
- Understanding of Just recipe syntax
- Familiarity with the confidantic devenv contract
- Access to `tree-sitter`, `cue`, and `jq` binaries

## Success Criteria

- [ ] All new Just recipes work correctly
- [ ] All required compatibility recipes remain functional
- [ ] `cue fmt` and `cue vet` are enforced (no bypass paths)
- [ ] Workshop one-shot recipe (`cue:from-ts:workshop`) works end-to-end
- [ ] Integration tests cover all recipe paths
- [ ] Documentation updated with recipe usage examples
- [ ] Backward compatibility maintained

## Task Breakdown

### Track A: Just Recipe Implementation (3-4 days)

#### A1. Update `scripts/confidantic.just`

**Deliverables**:

1. **Add workshop recipe variables**
   ```just
   # Workshop configuration
   confidantic_root := env_var_or_default('CONFIDANTIC_ROOT', '.devman/.config')
   build_dir := env_var_or_default('CONFIDANTIC_BUILD_DIR', 'build')
   schemas_dir := build_dir + '/schemas/cue'
   treesitter_dir := build_dir + '/treesitter'
   ```

2. **Recipe: `cue:from-ts:generate <grammar>`**
   ```just
   # Generate CUE schemas from Tree-sitter artifacts
   cue:from-ts:generate GRAMMAR:
       @echo "Generating CUE schemas for grammar: {{ GRAMMAR }}"
       @confidantic workshop generate \
           --grammar {{ GRAMMAR }} \
           --node-types {{ treesitter_dir }}/{{ GRAMMAR }}/node-types.json \
           --queries-dir {{ treesitter_dir }}/{{ GRAMMAR }}/queries \
           --output-dir {{ schemas_dir }}/{{ GRAMMAR }}
   ```

   **Requirements**:
   - Check that input files exist before running
   - Create output directory if missing
   - Log event to `logs/workshop.jsonl`
   - Exit with error if generation fails

3. **Recipe: `cue:from-ts:fmt <grammar>`**
   ```just
   # Format generated CUE schemas with cue fmt
   cue:from-ts:fmt GRAMMAR:
       @echo "Formatting CUE schemas for grammar: {{ GRAMMAR }}"
       @find {{ schemas_dir }}/{{ GRAMMAR }} -name '*.cue' -type f \
           -exec cue fmt {} \;
   ```

   **Requirements**:
   - Run `cue fmt` on all `.cue` files in grammar directory
   - Fail if any file fails to format
   - Preserve file modification times where possible

4. **Recipe: `cue:from-ts:vet <grammar>`**
   ```just
   # Validate generated CUE schemas with cue vet
   cue:from-ts:vet GRAMMAR:
       @echo "Validating CUE schemas for grammar: {{ GRAMMAR }}"
       @cue vet {{ schemas_dir }}/{{ GRAMMAR }}/...
   ```

   **Requirements**:
   - Run `cue vet` on all CUE in grammar directory
   - Display validation errors clearly
   - Exit with non-zero code on validation failure

5. **Recipe: `cue:from-ts:test <grammar>`**
   ```just
   # Run tests on generated CUE schemas
   cue:from-ts:test GRAMMAR:
       @echo "Testing CUE schemas for grammar: {{ GRAMMAR }}"
       @pytest tests/integration/workshop/test_{{ GRAMMAR }}.py -v
   ```

   **Requirements**:
   - Run grammar-specific integration tests
   - Skip if test file doesn't exist (with warning)
   - Display test results clearly

6. **Recipe: `cue:from-ts:doctor <grammar>`**
   ```just
   # Run diagnostics on Tree-sitter artifacts and generated CUE
   cue:from-ts:doctor GRAMMAR:
       @echo "Running diagnostics for grammar: {{ GRAMMAR }}"
       @confidantic workshop doctor \
           --grammar {{ GRAMMAR }} \
           --node-types {{ treesitter_dir }}/{{ GRAMMAR }}/node-types.json \
           --queries-dir {{ treesitter_dir }}/{{ GRAMMAR }}/queries \
           --schemas-dir {{ schemas_dir }}/{{ GRAMMAR }}
   ```

   **Requirements**:
   - Check for missing artifacts
   - Check for unmapped captures
   - Check for orphaned node references
   - Report deterministic diff warnings
   - Exit 0 even if warnings found (diagnostic only)

7. **Recipe: `cue:from-ts:workshop <grammar>` (One-shot workflow)**
   ```just
   # Complete workshop workflow: generate -> fmt -> vet -> test -> doctor
   cue:from-ts:workshop GRAMMAR:
       @echo "Running complete workshop for grammar: {{ GRAMMAR }}"
       just cue:from-ts:generate {{ GRAMMAR }}
       just cue:from-ts:fmt {{ GRAMMAR }}
       just cue:from-ts:vet {{ GRAMMAR }}
       just cue:from-ts:test {{ GRAMMAR }} || true
       just cue:from-ts:doctor {{ GRAMMAR }}
       @echo "✓ Workshop complete for {{ GRAMMAR }}"
   ```

   **Requirements**:
   - Run all steps in sequence
   - Stop on first critical failure (generate/fmt/vet)
   - Continue on test failure (non-critical)
   - Always run doctor at the end
   - Log complete workflow event

8. **Recipe: `cue:from-ts:clean <grammar>`**
   ```just
   # Clean generated CUE schemas for a grammar
   cue:from-ts:clean GRAMMAR:
       @echo "Cleaning generated schemas for {{ GRAMMAR }}"
       @rm -rf {{ schemas_dir }}/{{ GRAMMAR }}
       @echo "✓ Cleaned {{ schemas_dir }}/{{ GRAMMAR }}"
   ```

**Testing Requirements**:
- Test each recipe individually
- Test with valid Tree-sitter artifacts
- Test with missing input files (should error)
- Test with invalid CUE (vet should fail)
- Test workshop recipe end-to-end

---

#### A2. Maintain Required Compatibility Recipes

**Deliverables**:

Ensure these recipes continue to work (may need updates):

1. **`schema:export`** - Export Pydantic models to CUE
2. **`schema:vet`** - Validate resolved config against schemas
3. **`data:vet`** - Validate datasets against schemas
4. **`config:validate`** - Validate configuration
5. **`config:dump`** - Dump resolved config
6. **`config:env`** - Export environment variables
7. **`config:fingerprint`** - Generate configuration fingerprint

**Requirements**:
- Verify each recipe still works
- Update paths if needed (use new variables)
- Maintain backward compatibility
- Add tests for each recipe

**Testing Requirements**:
- Run each recipe and verify it works
- Test with existing configuration files
- Verify output format hasn't changed
- Test error paths

---

### Track B: CLI Plumbing Commands (Parallel with Track A)

**Estimated effort**: 2-3 days

#### B1. Add Workshop CLI Commands

Create `src/confidantic/cli/workshop.py`:

**Deliverables**:

1. **`confidantic workshop generate` command**
   ```python
   @app.command()
   def generate(
       grammar: str = typer.Option(..., help="Grammar name"),
       node_types: Path = typer.Option(..., help="Path to node-types.json"),
       queries_dir: Path = typer.Option(..., help="Directory with .scm query files"),
       output_dir: Path = typer.Option(..., help="Output directory for CUE schemas"),
   ) -> None:
       """Generate CUE schemas from Tree-sitter artifacts."""
   ```

   **Requirements**:
   - Load WorkshopInput using Phase 1 loaders
   - Generate CUE using Phase 2 generator
   - Log event to workshop.jsonl
   - Exit 0 on success, 1 on failure
   - Display rich progress output

2. **`confidantic workshop doctor` command**
   ```python
   @app.command()
   def doctor(
       grammar: str = typer.Option(..., help="Grammar name"),
       node_types: Path = typer.Option(..., help="Path to node-types.json"),
       queries_dir: Path = typer.Option(..., help="Directory with .scm query files"),
       schemas_dir: Path = typer.Option(None, help="Generated schemas directory"),
   ) -> None:
       """Run diagnostics on Tree-sitter artifacts and schemas."""
   ```

   **Requirements**:
   - Check for missing files
   - Check for unmapped captures
   - Check for orphaned references
   - Display warnings with rich formatting
   - Exit 0 (diagnostic only, not an error)

3. **`confidantic workshop validate` command**
   ```python
   @app.command()
   def validate(
       grammar: str = typer.Option(..., help="Grammar name"),
       schemas_dir: Path = typer.Option(..., help="Schemas directory"),
   ) -> None:
       """Validate generated CUE schemas with cue vet."""
   ```

   **Requirements**:
   - Run cue vet on schemas
   - Display validation results
   - Exit 0 on success, 1 on validation errors

**Testing Requirements**:
- Test each command with valid inputs
- Test with missing files
- Test with invalid artifacts
- Test error messages are clear
- Test exit codes are correct

---

#### B2. Create CUE Wrapper Module

Create `src/confidantic/cue/wrapper.py`:

**Deliverables**:

1. **`run_cue_fmt()` function**
   ```python
   def run_cue_fmt(
       file_or_dir: Path,
       check: bool = False
   ) -> subprocess.CompletedProcess:
       """
       Run cue fmt on file or directory.

       Args:
           file_or_dir: Path to .cue file or directory
           check: If True, check formatting without modifying files

       Returns:
           CompletedProcess with stdout/stderr

       Raises:
           subprocess.CalledProcessError: If cue fmt fails
       """
   ```

2. **`run_cue_vet()` function**
   ```python
   def run_cue_vet(
       path: Path,
       schema: Path | None = None
   ) -> subprocess.CompletedProcess:
       """
       Run cue vet on path.

       Args:
           path: Path to .cue file or directory
           schema: Optional schema to validate against

       Returns:
           CompletedProcess with stdout/stderr

       Raises:
           subprocess.CalledProcessError: If validation fails
       """
   ```

3. **`check_cue_available()` function**
   ```python
   def check_cue_available() -> bool:
       """
       Check if cue binary is available in PATH.

       Returns:
           True if cue is available, False otherwise
       """
   ```

**Testing Requirements**:
- Test with valid CUE files
- Test with invalid CUE files
- Test with missing cue binary
- Test error handling and messages

---

### Track C: Integration Tests (After Tracks A and B)

**Estimated effort**: 2 days

#### C1. Create Integration Test Suite

Create `tests/integration/workshop/test_workflow_integration.py`:

**Deliverables**:

1. **Test complete workflow**
   ```python
   def test_workshop_workflow_end_to_end(sample_grammar_artifacts, tmp_path):
       """Test complete workshop workflow from artifacts to validated CUE."""
       # Setup
       grammar = "python"
       output_dir = tmp_path / "build/schemas/cue/python"

       # Step 1: Generate
       result = subprocess.run(
           ["confidantic", "workshop", "generate",
            "--grammar", grammar,
            "--node-types", str(sample_grammar_artifacts / "node-types.json"),
            "--queries-dir", str(sample_grammar_artifacts / "queries"),
            "--output-dir", str(output_dir)],
           capture_output=True,
           text=True
       )
       assert result.returncode == 0, f"Generate failed: {result.stderr}"

       # Step 2: Format
       result = subprocess.run(
           ["cue", "fmt", str(output_dir / "*.cue")],
           capture_output=True,
           shell=True
       )
       assert result.returncode == 0, f"Format failed: {result.stderr}"

       # Step 3: Validate
       result = subprocess.run(
           ["cue", "vet", str(output_dir / "...")],
           capture_output=True,
           text=True
       )
       assert result.returncode == 0, f"Validation failed: {result.stderr}"
   ```

2. **Test Just recipes**
   ```python
   def test_just_recipe_generate(sample_grammar_artifacts):
       """Test just cue:from-ts:generate recipe."""
       result = subprocess.run(
           ["just", "cue:from-ts:generate", "python"],
           capture_output=True,
           text=True
       )
       assert result.returncode == 0, f"Recipe failed: {result.stderr}"
   ```

3. **Test error handling**
   ```python
   def test_workflow_handles_missing_input():
       """Test workflow fails gracefully with missing inputs."""
       result = subprocess.run(
           ["confidantic", "workshop", "generate",
            "--grammar", "nonexistent",
            "--node-types", "/nonexistent/path",
            "--queries-dir", "/nonexistent/path",
            "--output-dir", "/tmp/output"],
           capture_output=True,
           text=True
       )
       assert result.returncode != 0
       assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()
   ```

**Testing Requirements**:
- Test all recipes individually
- Test workshop one-shot recipe
- Test error paths
- Test with multiple grammars
- Verify JSONL logging works

---

#### C2. Test Required Compatibility Recipes

Create `tests/integration/test_compatibility_recipes.py`:

**Deliverables**:

1. **Test each required recipe**
   ```python
   def test_schema_export_recipe():
       """Test schema:export recipe still works."""
       result = subprocess.run(
           ["just", "schema:export"],
           capture_output=True,
           text=True
       )
       assert result.returncode == 0

   def test_config_validate_recipe():
       """Test config:validate recipe still works."""
       result = subprocess.run(
           ["just", "config:validate"],
           capture_output=True,
           text=True
       )
       assert result.returncode == 0

   # Similar tests for other required recipes...
   ```

**Testing Requirements**:
- Test all 7 required recipes
- Verify outputs match expected format
- Test with various configurations
- Ensure backward compatibility

---

## Parallelization Strategy

### Week 1 (Parallel Development)

**Developer A**:
- Track A: Implement Just recipes (A1)
- Test workshop recipes
- Update recipe documentation

**Developer B**:
- Track B: Implement CLI commands (B1)
- Implement CUE wrapper utilities (B2)
- Test CLI commands

**Sync Point**: Both developers integrate CLI + Just recipes

### Week 2 (Integration & Testing)

**Both developers**:
- Track C1: Integration tests
- Track C2: Compatibility tests
- Fix any issues discovered
- Documentation updates

---

## Testing Strategy

### Unit Tests (CLI Commands)

For each CLI command:
- Test with valid inputs
- Test with missing files
- Test with invalid data
- Test exit codes
- Test output formatting

### Integration Tests (Just Recipes)

For each recipe:
- Test with valid grammar
- Test with missing artifacts
- Test error handling
- Test output paths
- Test logging

### End-to-End Tests (Complete Workflow)

- Run workshop recipe on real grammar
- Verify all steps execute correctly
- Verify CUE is valid and formatted
- Verify JSONL logs are created
- Test with multiple grammars in sequence

### Compatibility Tests (Required Recipes)

- Run each required recipe
- Verify functionality unchanged
- Test with existing configurations
- Verify output format stable

---

## Verification Checklist

Before marking Phase 3 complete, verify:

### Just Recipes
- [ ] All new workshop recipes work correctly
- [ ] All required compatibility recipes still work
- [ ] Recipes handle errors gracefully
- [ ] Recipe documentation is complete
- [ ] Recipes use correct paths (via variables)

### CLI Commands
- [ ] All workshop commands work correctly
- [ ] Commands validate inputs before processing
- [ ] Error messages are clear and actionable
- [ ] Exit codes are correct (0 = success, 1 = error)
- [ ] Rich output is formatted correctly

### CUE Integration
- [ ] `cue fmt` runs successfully on generated files
- [ ] `cue vet` validates generated files
- [ ] No bypass paths for CUE requirements
- [ ] CUE errors are displayed clearly

### Testing
- [ ] All integration tests pass
- [ ] All compatibility tests pass
- [ ] End-to-end workflow test passes
- [ ] Error path tests pass
- [ ] Code coverage ≥ 85% for new code

### Documentation
- [ ] Recipe usage documented in README
- [ ] CLI commands documented
- [ ] Example workflows included
- [ ] Migration notes updated

### Backward Compatibility
- [ ] All required recipes still work
- [ ] Configuration file format unchanged
- [ ] Existing Just recipes unaffected
- [ ] Devenv contract maintained

---

## Common Pitfalls to Avoid

1. **Breaking required recipes**: Always test compatibility recipes
2. **Hardcoded paths**: Use Just variables for all paths
3. **Silent failures**: Recipes must exit non-zero on failure
4. **Missing error messages**: All errors must be clear and actionable
5. **Bypassing CUE**: Never allow generation without fmt/vet
6. **Concurrent access**: Handle log file writes safely
7. **Platform differences**: Test on Linux and macOS

---

## Required Recipe Contracts

These recipes MUST remain available and functional:

### Configuration Recipes
- `config:validate` - Validate configuration files
- `config:dump` - Dump resolved configuration (redacted)
- `config:env` - Export environment variables
- `config:fingerprint` - Generate config fingerprint

### Schema Recipes
- `schema:export` - Export Pydantic models to CUE
- `schema:vet` - Validate config against schemas
- `data:vet` - Validate datasets against schemas

**Important**: These recipes may need path updates, but their behavior and output format must remain consistent.

---

## New Recipe Naming Convention

All new workshop recipes follow this pattern:
```
cue:from-ts:<action> <grammar>
```

Where `<action>` is one of:
- `generate` - Generate CUE from Tree-sitter
- `fmt` - Format CUE files
- `vet` - Validate CUE files
- `test` - Run tests
- `doctor` - Run diagnostics
- `workshop` - Complete workflow
- `clean` - Clean generated files

This naming makes it clear these recipes are for Tree-sitter-to-CUE workflow.

---

## Example Usage (After Phase 3)

### Using Just Recipes (Recommended)

```bash
# Generate CUE for Python grammar
just cue:from-ts:generate python

# Format generated CUE
just cue:from-ts:fmt python

# Validate generated CUE
just cue:from-ts:vet python

# Run complete workflow (one-shot)
just cue:from-ts:workshop python

# Run diagnostics
just cue:from-ts:doctor python

# Clean generated files
just cue:from-ts:clean python
```

### Using CLI Directly (Plumbing)

```bash
# Generate CUE (plumbing only)
confidantic workshop generate \
  --grammar python \
  --node-types build/treesitter/python/node-types.json \
  --queries-dir build/treesitter/python/queries \
  --output-dir build/schemas/cue/python

# Run diagnostics
confidantic workshop doctor \
  --grammar python \
  --node-types build/treesitter/python/node-types.json \
  --queries-dir build/treesitter/python/queries \
  --schemas-dir build/schemas/cue/python
```

### Using Required Recipes (Compatibility)

```bash
# Existing recipes still work
just config:validate
just schema:export
just schema:vet
```

---

## Exit Criteria

Phase 3 is complete when:

1. All new workshop Just recipes work correctly
2. All required compatibility recipes remain functional
3. CLI workshop commands work correctly
4. CUE formatting and validation are enforced
5. Integration tests pass (workshop + compatibility)
6. End-to-end workflow test passes
7. Documentation is complete
8. All items in verification checklist are checked off

**Next Phase**: Phase 4 - Doctoring, diagnostics, and provenance

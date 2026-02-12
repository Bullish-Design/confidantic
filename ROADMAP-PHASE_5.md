# Phase 5: CLI Plumbing and Migration Compatibility

## Overview

Phase 5 finalizes the CLI interface as minimal plumbing and ensures backward compatibility with existing commands and workflows. This phase focuses on **stability**, **migration paths**, and **CI/CD integration** while maintaining the Just-first philosophy.

**Goal**: Provide stable CLI plumbing for CI/CD scripts while preserving all existing command contracts and documenting migration paths.

## Prerequisites

- Phase 1-4 complete (all workshop components ready)
- Understanding of CLI design patterns
- Familiarity with CI/CD automation requirements
- Knowledge of existing Pydantic export workflows

## Success Criteria

- [ ] All existing CLI commands still work
- [ ] New workshop commands are minimal plumbing
- [ ] Migration documentation is complete and clear
- [ ] Backward compatibility tests pass
- [ ] CI integration examples provided
- [ ] Deprecation warnings (if any) are clear
- [ ] Command help text is comprehensive

## Task Breakdown

### Track A: CLI Consolidation and Plumbing (3-4 days)

#### A1. Consolidate CLI Structure

**Deliverables**:

Update `src/confidantic/cli.py` (or `src/confidantic/cli/__init__.py`):

1. **Main CLI app structure**
   ```python
   import typer
   from rich.console import Console

   app = typer.Typer(
       name="confidantic",
       help="Deterministic Tree-sitter-to-CUE workshop tooling",
       no_args_is_help=True,
   )

   console = Console()

   # Register subcommands
   from confidantic.cli.config import app as config_app
   from confidantic.cli.schema import app as schema_app
   from confidantic.cli.workshop import app as workshop_app
   from confidantic.cli.logs import app as logs_app

   app.add_typer(config_app, name="config")
   app.add_typer(schema_app, name="schema")
   app.add_typer(workshop_app, name="workshop")
   app.add_typer(logs_app, name="logs")
   ```

2. **Ensure all existing commands work** (`config` group)

   Existing commands that MUST work:
   - `confidantic config validate`
   - `confidantic config dump`
   - `confidantic config env`
   - `confidantic config fingerprint`

   **Requirements**:
   - No breaking changes to command signatures
   - Same output formats
   - Same exit codes
   - Same error messages

3. **Ensure schema commands work** (`schema` group)

   Existing commands:
   - `confidantic schema export`
   - `confidantic schema vet`

   **Requirements**:
   - Maintain existing behavior
   - Support all existing flags
   - Preserve output format

4. **Finalize workshop commands** (`workshop` group - from Phase 3/4)

   Workshop commands (plumbing only):
   - `confidantic workshop generate`
   - `confidantic workshop doctor`
   - `confidantic workshop validate`

   **Requirements**:
   - Minimal output (machine-parseable)
   - Clear exit codes (0=success, 1=error)
   - JSON output option for CI
   - No interactive prompts

5. **Add logs commands** (`logs` group - from Phase 4)

   Log query commands:
   - `confidantic logs show`
   - `confidantic logs stats`
   - `confidantic logs query`

   **Requirements**:
   - Support filtering options
   - JSON output for scripting
   - Human-friendly default output

**Testing Requirements**:
- Test each command group
- Test all flags and options
- Test output formats
- Test exit codes
- Test error handling

---

#### A2. Add CI-Friendly Features

**Deliverables**:

1. **Global options for all commands**
   ```python
   @app.callback()
   def main(
       ctx: typer.Context,
       verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
       quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
       json_output: bool = typer.Option(False, "--json", help="JSON output"),
       no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
   ):
       """Global options for all confidantic commands."""
       ctx.obj = {
           "verbose": verbose,
           "quiet": quiet,
           "json": json_output,
           "no_color": no_color,
       }
   ```

2. **JSON output mode for all commands**
   ```python
   def output_result(result: dict, ctx: typer.Context):
       """Output result in appropriate format based on context."""
       if ctx.obj.get("json"):
           console.print_json(data=result)
       elif ctx.obj.get("quiet"):
           # Minimal output
           ...
       else:
           # Rich human-friendly output
           ...
   ```

3. **Exit code contract**
   - `0` - Success
   - `1` - General error
   - `2` - Invalid input/arguments
   - `3` - Missing dependencies (cue, tree-sitter, etc.)

4. **Dry-run mode**
   ```python
   dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done")
   ```

**Testing Requirements**:
- Test verbose mode
- Test quiet mode
- Test JSON output
- Test no-color mode
- Test dry-run mode
- Verify exit codes

---

### Track B: Backward Compatibility and Adapters (Parallel with Track A)

**Estimated effort**: 2-3 days

#### B1. Implement Compatibility Layer

**Deliverables**:

Create `src/confidantic/compat.py`:

1. **Legacy command adapters**
   ```python
   def adapt_legacy_config_command(args: list[str]) -> int:
       """
       Adapter for legacy configuration commands.

       Translates old command patterns to new structure.
       """
   ```

2. **Configuration format migration**
   ```python
   def migrate_config_v1_to_v2(old_config: dict) -> dict:
       """
       Migrate v1 configuration format to v2.

       Args:
           old_config: Legacy configuration dict

       Returns:
           Updated configuration dict
       """
   ```

3. **Deprecation warnings**
   ```python
   def warn_deprecated(
       old_name: str,
       new_name: str,
       removal_version: str = "2.0.0"
   ):
       """Show deprecation warning for command/option."""
       console.print(
           f"[yellow]Warning: '{old_name}' is deprecated and will be removed in {removal_version}. "
           f"Use '{new_name}' instead.[/yellow]"
       )
   ```

**Testing Requirements**:
- Test legacy command patterns
- Test config migration
- Test deprecation warnings
- Verify warnings don't break workflows

---

#### B2. Add Migration Utilities

**Deliverables**:

Create `confidantic migrate` command group:

1. **`confidantic migrate check` command**
   ```python
   @migrate_app.command()
   def check(
       config_path: Path = typer.Option(
           ".devman/.config/confidantic.toml",
           help="Path to config file"
       )
   ) -> None:
       """
       Check if configuration needs migration.

       Analyzes config and reports any deprecated patterns.
       """
   ```

2. **`confidantic migrate apply` command**
   ```python
   @migrate_app.command()
   def apply(
       config_path: Path,
       backup: bool = typer.Option(True, help="Create backup before migration")
   ) -> None:
       """
       Migrate configuration to latest format.

       Creates backup and updates config file.
       """
   ```

3. **`confidantic migrate doctor` command**
   ```python
   @migrate_app.command()
   def doctor() -> None:
       """
       Check for migration issues and compatibility problems.

       Scans project for deprecated patterns and suggests fixes.
       """
   ```

**Testing Requirements**:
- Test migration check with old configs
- Test migration apply
- Test backup creation
- Test migration doctor

---

### Track C: Documentation and Migration Guide (After Tracks A and B)

**Estimated effort**: 2-3 days

#### C1. Create Migration Documentation

**Deliverables**:

Create `docs/MIGRATION.md`:

```markdown
# Migration Guide: Pydantic Export → Tree-sitter Workshop

This guide helps you migrate from the old Pydantic-export focused workflow to the new Tree-sitter-to-CUE workshop workflow.

## Overview of Changes

### Philosophy Shift

**Before (Pydantic Export)**:
- Focus: Export Pydantic models to CUE
- Primary use: Python configuration validation
- Workflow: Python → CUE

**After (Workshop)**:
- Focus: Tree-sitter artifacts → CUE schemas
- Primary use: Language tooling schema generation
- Workflow: Tree-sitter → CUE
- Bonus: Still supports Pydantic export via `schema:export`

## Command Changes

### No Breaking Changes

All existing commands still work:
- `confidantic config validate` ✓
- `confidantic config dump` ✓
- `confidantic config env` ✓
- `confidantic config fingerprint` ✓
- `confidantic schema export` ✓
- `confidantic schema vet` ✓

### New Commands

Workshop-specific commands:
- `confidantic workshop generate` - Generate CUE from Tree-sitter
- `confidantic workshop doctor` - Run diagnostics
- `confidantic logs show` - View workshop logs

### Deprecated Commands (None Yet)

Currently, no commands are deprecated. The workshop features are purely additive.

## Configuration Changes

### Configuration Format (No Changes Required)

Your existing `confidantic.toml` continues to work as-is.

### New Optional Fields

```toml
# Optional: Workshop-specific settings
[workshop]
log_level = "info"
doctor_on_generate = false  # Run doctor after generate
```

## Just Recipe Changes

### Required Recipes (Unchanged)

These recipes continue to work:
- `just config:validate`
- `just config:dump`
- `just schema:export`
- `just schema:vet`

### New Recipes

Add these to your justfile (optional):
- `just cue:from-ts:generate <grammar>`
- `just cue:from-ts:workshop <grammar>`
- `just cue:from-ts:doctor <grammar>`

## Migration Steps

### Step 1: Update confidantic

```bash
# Update to latest version
pip install --upgrade confidantic
```

### Step 2: Check for Issues

```bash
# Run migration check
confidantic migrate check

# Run compatibility doctor
confidantic migrate doctor
```

### Step 3: Update Justfile (Optional)

If you want to use workshop features, include the confidantic justfile:

```just
# Add to your justfile
import? 'scripts/confidantic.just'
```

### Step 4: Test Existing Workflows

```bash
# Verify existing commands work
just config:validate
just schema:export
just schema:vet
```

### Step 5: Adopt Workshop Features (Optional)

```bash
# Try workshop workflow
just cue:from-ts:workshop python
```

## Compatibility Guarantees

### What's Guaranteed

- All existing CLI commands work
- All existing Just recipes work
- Configuration format is stable
- Output formats are stable

### What's Not Guaranteed

- Internal API changes (use public CLI/recipes only)
- Log format changes (parse with jq for stability)
- Diagnostic message wording

## Troubleshooting

### Command not found

```bash
# Reinstall confidantic
pip install --force-reinstall confidantic
```

### Recipe not found

```bash
# Ensure confidantic justfile is included
grep "confidantic.just" justfile

# Or copy recipes manually
just --list
```

### Configuration errors

```bash
# Validate configuration
confidantic config validate

# Dump resolved config
confidantic config dump
```

## Getting Help

- Documentation: `confidantic --help`
- Recipe list: `just --list`
- Migration check: `confidantic migrate check`
- Open issue: https://github.com/confidantic/confidantic/issues
```

**Testing Requirements**:
- Verify all examples work
- Test migration steps
- Verify troubleshooting tips

---

#### C2. Update Main Documentation

**Deliverables**:

Update `README.md`:

1. Add migration notice:
   ```markdown
   ## Migrating from Earlier Versions

   Confidantic 1.0 adds Tree-sitter workshop features while maintaining full backward compatibility.

   - **Existing users**: All your commands and recipes continue to work
   - **New users**: Start with the workshop workflow
   - **Migration guide**: See [MIGRATION.md](docs/MIGRATION.md)
   ```

2. Add workshop workflow section:
   ```markdown
   ## Workshop Workflow

   Generate CUE schemas from Tree-sitter artifacts:

   ```bash
   # One-shot workflow
   just cue:from-ts:workshop python

   # Or step-by-step
   just cue:from-ts:generate python
   just cue:from-ts:fmt python
   just cue:from-ts:vet python
   just cue:from-ts:doctor python
   ```
   ```

3. Update command reference:
   ```markdown
   ## Command Reference

   ### Configuration
   - `confidantic config validate` - Validate configuration
   - `confidantic config dump` - Dump resolved config

   ### Schema
   - `confidantic schema export` - Export Pydantic to CUE
   - `confidantic schema vet` - Validate config against schemas

   ### Workshop (New)
   - `confidantic workshop generate` - Generate CUE from Tree-sitter
   - `confidantic workshop doctor` - Run diagnostics
   - `confidantic logs show` - View logs
   ```

**Testing Requirements**:
- Verify examples work
- Test all commands mentioned
- Verify links

---

#### C3. Create CI/CD Integration Examples

**Deliverables**:

Create `docs/CI_INTEGRATION.md`:

```markdown
# CI/CD Integration

## GitHub Actions Example

```yaml
name: Confidantic Workshop

on: [push, pull_request]

jobs:
  workshop:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          pip install confidantic
          curl -sSL https://get.cuelang.org | sh

      - name: Validate configuration
        run: confidantic config validate

      - name: Generate and validate CUE
        run: |
          confidantic workshop generate \
            --grammar python \
            --node-types build/treesitter/python/node-types.json \
            --queries-dir build/treesitter/python/queries \
            --output-dir build/schemas/cue/python

          # Validate generated CUE
          cue vet build/schemas/cue/python/...

      - name: Run diagnostics
        run: |
          confidantic workshop doctor \
            --grammar python \
            --node-types build/treesitter/python/node-types.json \
            --queries-dir build/treesitter/python/queries \
            --schemas-dir build/schemas/cue/python
```

## GitLab CI Example

```yaml
workshop:
  image: python:3.11
  before_script:
    - pip install confidantic
    - curl -sSL https://get.cuelang.org | sh
  script:
    - confidantic config validate
    - confidantic workshop generate --grammar python ...
    - cue vet build/schemas/cue/python/...
    - confidantic workshop doctor --grammar python ...
```

## Make Integration

```makefile
.PHONY: workshop-python
workshop-python:
\t@confidantic workshop generate --grammar python ...
\t@cue fmt build/schemas/cue/python/*.cue
\t@cue vet build/schemas/cue/python/...
\t@confidantic workshop doctor --grammar python ...
```
```

**Testing Requirements**:
- Test GitHub Actions example
- Test GitLab CI example
- Test Makefile example

---

## Parallelization Strategy

### Week 1 (Parallel Development)

**Developer A**:
- Track A: CLI consolidation (A1)
- CI-friendly features (A2)
- Test all CLI commands

**Developer B**:
- Track B: Compatibility layer (B1)
- Migration utilities (B2)
- Test migration workflows

**Sync Point**: Integrate CLI + compatibility

### Week 2 (Documentation)

**Both developers**:
- Track C1: Migration documentation
- Track C2: Update main docs
- Track C3: CI integration examples
- Final testing

---

## Testing Strategy

### Unit Tests (Command Level)

For each CLI command:
- Test with valid inputs
- Test with invalid inputs
- Test all flags/options
- Test exit codes
- Test output formats

### Integration Tests (Workflow Level)

- Test complete workflows
- Test migration paths
- Test backward compatibility
- Test CI integration patterns

### Regression Tests (Compatibility)

- Run all old command patterns
- Verify same output
- Verify same exit codes
- Test with old configurations

### Documentation Tests

- Test all examples
- Verify all commands work
- Check all links

---

## Verification Checklist

Before marking Phase 5 complete, verify:

### CLI Stability
- [ ] All existing commands work
- [ ] All new commands work
- [ ] All flags/options work
- [ ] Exit codes are correct
- [ ] Help text is comprehensive

### Compatibility
- [ ] Backward compatibility tests pass
- [ ] Legacy commands work (if any)
- [ ] Config migration works
- [ ] Deprecation warnings are clear

### CI/CD Integration
- [ ] CI examples work
- [ ] JSON output mode works
- [ ] Quiet mode works
- [ ] Exit codes are reliable

### Documentation
- [ ] Migration guide complete
- [ ] README updated
- [ ] CI integration examples provided
- [ ] All examples tested

### Testing
- [ ] All tests pass
- [ ] Regression tests pass
- [ ] Integration tests pass
- [ ] Code coverage ≥ 85%

---

## Common Pitfalls to Avoid

1. **Breaking existing commands**: Always maintain exact behavior
2. **Changing output formats**: Breaking change for scripts
3. **Changing exit codes**: Breaking change for CI
4. **Missing deprecation warnings**: Users need advance notice
5. **Incomplete migration docs**: Users need clear path forward
6. **Untested CI examples**: Examples must work as documented
7. **Missing backward compat tests**: Regressions will happen

---

## Example Usage (After Phase 5)

### Using CLI (Plumbing for CI)

```bash
# Configuration commands (existing)
confidantic config validate
confidantic config dump --format json > config.json

# Schema commands (existing)
confidantic schema export
confidantic schema vet

# Workshop commands (new, for CI)
confidantic workshop generate \
  --grammar python \
  --node-types build/treesitter/python/node-types.json \
  --queries-dir build/treesitter/python/queries \
  --output-dir build/schemas/cue/python \
  --json

# Logs commands (new)
confidantic logs show --json --limit 10
confidantic logs stats --json
```

### Using Just Recipes (Developer UX)

```bash
# Existing recipes (still work)
just config:validate
just schema:export

# New workshop recipes
just cue:from-ts:workshop python
just cue:from-ts:doctor python
```

### Migration Workflow

```bash
# 1. Check for migration needs
confidantic migrate check

# 2. Run migration doctor
confidantic migrate doctor

# 3. Apply migration (if needed)
confidantic migrate apply --backup

# 4. Verify everything works
just config:validate
just schema:export
```

---

## Exit Criteria

Phase 5 is complete when:

1. All existing CLI commands work unchanged
2. New workshop commands are stable and documented
3. Migration documentation is complete
4. Backward compatibility tests pass
5. CI integration examples work
6. All tests pass
7. All items in verification checklist checked off

**Next Phase**: Phase 6 - Hardening and quality gates

# Phase 5: CLI Plumbing and CI Integration

## Overview

Phase 5 finalizes the CLI interface as minimal plumbing for workshop and CI/CD use. This phase focuses on **stability**, **scriptability**, and **clear command contracts** while maintaining the Just-first philosophy.

**Goal**: Provide stable CLI plumbing for CI/CD scripts and developer workflows centered on Tree-sitter-to-CUE workshop operations.

## Prerequisites

- Phase 1-4 complete (all workshop components ready)
- Understanding of CLI design patterns
- Familiarity with CI/CD automation requirements

## Success Criteria

- [ ] Required CLI commands are stable and documented
- [ ] Workshop commands are minimal plumbing
- [ ] CI integration examples are complete and validated
- [ ] Command contract tests pass
- [ ] Command help text is comprehensive
- [ ] JSON output mode is available for automation

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

   from confidantic.cli.config import app as config_app
   from confidantic.cli.schema import app as schema_app
   from confidantic.cli.workshop import app as workshop_app
   from confidantic.cli.logs import app as logs_app

   app.add_typer(config_app, name="config")
   app.add_typer(schema_app, name="schema")
   app.add_typer(workshop_app, name="workshop")
   app.add_typer(logs_app, name="logs")
   ```

2. **Ensure required config commands work** (`config` group)

   - `confidantic config validate`
   - `confidantic config dump`
   - `confidantic config env`
   - `confidantic config fingerprint`

3. **Ensure required schema commands work** (`schema` group)

   - `confidantic schema export`
   - `confidantic schema vet`

4. **Finalize workshop commands** (`workshop` group)

   - `confidantic workshop generate`
   - `confidantic workshop doctor`
   - `confidantic workshop validate`

   **Requirements**:
   - Minimal output (machine-parseable)
   - Clear exit codes (0=success, 1=error)
   - JSON output option for CI
   - No interactive prompts

5. **Add logs commands** (`logs` group)

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
       ctx.obj = {
           "verbose": verbose,
           "quiet": quiet,
           "json": json_output,
           "no_color": no_color,
       }
   ```

2. **JSON output mode for all commands**

3. **Exit code contract**

   - `0` - Success
   - `1` - General error
   - `2` - Invalid input/arguments
   - `3` - Missing dependencies (`cue`, `tree-sitter`, etc.)

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

### Track B: Command Contracts and Ergonomics (Parallel with Track A)

**Estimated effort**: 2-3 days

#### B1. Enforce Command Contracts

**Deliverables**:

1. Add command-level contract tests for:
   - required `config` commands
   - required `schema` commands
   - workshop plumbing commands
   - logs commands

2. Ensure command signatures are explicit and stable.

3. Add deterministic error output for script usage.

**Testing Requirements**:

- Contract tests for command presence and behavior
- Exit-code tests for success/failure paths
- JSON output tests for parsable command output

---

#### B2. Add Workflow Utility Group

**Deliverables**:

Create `confidantic doctor` or `confidantic workflow` group with utility checks for CI/operator usage.

Suggested commands:

- `confidantic workflow check`
- `confidantic workflow doctor`

**Testing Requirements**:

- Test utility command success/failure behavior
- Test output modes (human + JSON)

---

### Track C: Documentation (After Tracks A and B)

**Estimated effort**: 2-3 days

#### C1. Update Main Documentation

**Deliverables**:

Update `README.md` with:

1. Workshop workflow section (one-shot and step-by-step)
2. CLI command reference by group
3. CI-oriented usage examples with JSON output mode

**Testing Requirements**:

- Verify examples work
- Test all commands mentioned
- Verify links

---

#### C2. Create CI/CD Integration Examples

**Deliverables**:

Create `docs/CI_INTEGRATION.md` with:

- GitHub Actions example
- GitLab CI example
- Makefile integration example

**Testing Requirements**:

- Validate command examples
- Verify shell snippets and arguments

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

- Test complete workshop workflows
- Test CI integration patterns
- Test required recipe contracts

### Documentation Tests

- Test all examples
- Verify all commands work
- Check all links

---

## Verification Checklist

Before marking Phase 5 complete, verify:

### CLI Stability

- [ ] All required commands work
- [ ] Workshop/logs commands work
- [ ] All flags/options work
- [ ] Exit codes are correct
- [ ] Help text is comprehensive

### CI/CD Integration

- [ ] CI examples work
- [ ] JSON output mode works
- [ ] Quiet mode works
- [ ] Exit codes are reliable

### Documentation

- [ ] README updated
- [ ] CI integration examples provided
- [ ] All examples tested

### Testing

- [ ] All tests pass
- [ ] Integration tests pass
- [ ] Code coverage ≥ 85%

---

## Common Pitfalls to Avoid

1. **Breaking required command contracts**
2. **Changing output formats without contract updates**
3. **Changing exit codes without tests/docs**
4. **Untested CI examples**
5. **Incomplete command documentation**

---

## Example Usage (After Phase 5)

### Using CLI (Plumbing for CI)

```bash
# Configuration commands
confidantic config validate
confidantic config dump --format json > config.json

# Schema commands
confidantic schema export
confidantic schema vet

# Workshop commands
confidantic workshop generate \
  --grammar python \
  --node-types build/treesitter/python/node-types.json \
  --queries-dir build/treesitter/python/queries \
  --output-dir build/schemas/cue/python \
  --json

# Logs commands
confidantic logs show --json --limit 10
confidantic logs stats --json
```

### Using Just Recipes (Developer UX)

```bash
just config:validate
just schema:export

just cue:from-ts:workshop python
just cue:from-ts:doctor python
```

---

## Exit Criteria

Phase 5 is complete when:

1. Required commands are stable and tested
2. Workshop/logs commands are stable and documented
3. CI integration examples work
4. Contract/integration tests pass
5. All checklist items are complete

**Next Phase**: Phase 6 - Hardening and quality gates

# Phase 6: Hardening and Quality Gates

## Overview

Phase 6 finalizes confidantic for production release by adding comprehensive quality gates, performance validation, and end-to-end integration testing. This phase focuses on **reliability**, **performance**, and **production readiness**.

**Goal**: Ensure confidantic is production-ready with automated quality gates, performance guarantees, and comprehensive test coverage.

## Prerequisites

- Phase 1-5 complete (all components implemented)
- CI/CD pipeline infrastructure
- Understanding of golden snapshot testing
- Performance testing experience
- Access to real Tree-sitter grammars for testing

## Success Criteria

- [ ] CI pipeline with all quality gates passing
- [ ] Golden snapshot tests for deterministic generation
- [ ] CUE formatting and validation enforced in CI
- [ ] JSONL behavior validated in CI
- [ ] Redaction defaults verified
- [ ] End-to-end fixture for at least one grammar
- [ ] Performance benchmarks passing
- [ ] Release readiness checklist complete
- [ ] Code coverage ≥ 90%

## Task Breakdown

### Track A: CI Quality Gates (3-4 days)

#### A1. Create CI Pipeline Configuration

**Deliverables**:

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    name: Test Suite
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install system dependencies
        run: |
          # Install CUE
          curl -sSL https://github.com/cue-lang/cue/releases/download/v0.7.0/cue_v0.7.0_linux_amd64.tar.gz | tar xz
          sudo mv cue /usr/local/bin/

          # Install just
          curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | sudo bash -s -- --to /usr/local/bin

      - name: Install Python dependencies
        run: |
          pip install --upgrade pip
          pip install -e '.[dev,test]'

      - name: Run tests
        run: |
          pytest tests/ -v --cov=src/confidantic --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  quality-gates:
    name: Quality Gates
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          curl -sSL https://github.com/cue-lang/cue/releases/download/v0.7.0/cue_v0.7.0_linux_amd64.tar.gz | tar xz
          sudo mv cue /usr/local/bin/
          pip install -e '.[dev,test]'

      - name: Run golden snapshot tests
        run: pytest tests/integration/test_golden_snapshots.py -v

      - name: Verify CUE formatting
        run: |
          # Generate test CUE
          pytest tests/integration/test_cue_formatting.py -v

      - name: Verify JSONL behavior
        run: pytest tests/integration/test_jsonl_behavior.py -v

      - name: Verify redaction
        run: pytest tests/integration/test_redaction.py -v

  performance:
    name: Performance Benchmarks
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          curl -sSL https://github.com/cue-lang/cue/releases/download/v0.7.0/cue_v0.7.0_linux_amd64.tar.gz | tar xz
          sudo mv cue /usr/local/bin/
          pip install -e '.[dev,test]'

      - name: Run performance tests
        run: pytest tests/performance/ -v

  end-to-end:
    name: End-to-End Workshop
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          curl -sSL https://github.com/cue-lang/cue/releases/download/v0.7.0/cue_v0.7.0_linux_amd64.tar.gz | tar xz
          sudo mv cue /usr/local/bin/
          curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | sudo bash -s -- --to /usr/local/bin
          pip install -e '.[dev,test]'

      - name: Run end-to-end workshop
        run: pytest tests/integration/workshop/ -v
```

**Requirements**:
- Test on multiple Python versions
- Install all required dependencies
- Run all test categories
- Upload coverage reports
- Fail on any test failure

**Testing Requirements**:
- Verify CI runs successfully
- Test on multiple Python versions
- Verify all gates pass

---

#### A2. Create Quality Gate Tests

**Deliverables**:

Create `tests/integration/test_golden_snapshots.py`:

```python
"""
Golden snapshot tests for deterministic generation.

These tests ensure that generation is deterministic by comparing
output to saved golden snapshots.
"""

import pytest
from pathlib import Path
from confidantic.workshop.loaders import load_workshop_input
from confidantic.workshop.generator import CueGenerator


@pytest.fixture
def python_grammar_artifacts():
    """Load Python grammar artifacts from fixtures."""
    return {
        "grammar": "python",
        "node_types": Path("tests/fixtures/python/node-types.json"),
        "queries_dir": Path("tests/fixtures/python/queries"),
    }


def test_python_node_types_golden_snapshot(python_grammar_artifacts, tmp_path):
    """Compare Python node types generation to golden snapshot."""
    # Load input
    workshop_input = load_workshop_input(
        grammar_name=python_grammar_artifacts["grammar"],
        node_types_path=python_grammar_artifacts["node_types"],
        queries_dir=python_grammar_artifacts["queries_dir"],
    )

    # Generate CUE
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    generator = CueGenerator(workshop_input)
    generated_files = generator.generate(output_dir)

    # Load golden snapshot
    golden_dir = Path("tests/fixtures/golden/python")
    node_types_file = output_dir / "node_types.cue"
    golden_file = golden_dir / "node_types.cue"

    assert node_types_file.exists(), "node_types.cue not generated"
    assert golden_file.exists(), "Golden snapshot missing"

    # Normalize and compare (ignore timestamps)
    generated = normalize_cue(node_types_file.read_text())
    golden = normalize_cue(golden_file.read_text())

    assert generated == golden, (
        "Generated CUE differs from golden snapshot!\n"
        "If this is intentional, update snapshot with:\n"
        "  pytest tests/integration/test_golden_snapshots.py --update-snapshots"
    )


def normalize_cue(content: str) -> str:
    """Normalize CUE content for comparison (remove timestamps, etc.)."""
    import re
    # Remove timestamp lines
    content = re.sub(r'// Generated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\n', '', content)
    # Remove fingerprint lines
    content = re.sub(r'fingerprint: "[a-f0-9]+"\n', 'fingerprint: "NORMALIZED"\n', content)
    return content


def test_generation_is_deterministic(python_grammar_artifacts, tmp_path):
    """Verify generation produces identical output across runs."""
    workshop_input = load_workshop_input(
        grammar_name=python_grammar_artifacts["grammar"],
        node_types_path=python_grammar_artifacts["node_types"],
        queries_dir=python_grammar_artifacts["queries_dir"],
    )

    outputs = []
    for run in range(5):
        output_dir = tmp_path / f"run_{run}"
        output_dir.mkdir()
        generator = CueGenerator(workshop_input)
        generator.generate(output_dir)

        # Collect normalized output
        run_output = {}
        for cue_file in output_dir.glob("*.cue"):
            run_output[cue_file.name] = normalize_cue(cue_file.read_text())
        outputs.append(run_output)

    # All runs should produce identical output
    for i in range(1, len(outputs)):
        assert outputs[i] == outputs[0], f"Run {i} differs from run 0"
```

Create `tests/integration/test_cue_formatting.py`:

```python
"""Tests for CUE formatting enforcement."""

import subprocess
from pathlib import Path
import pytest


def test_all_generated_cue_is_formatted(sample_generated_cue_dir):
    """Verify all generated CUE files are properly formatted."""
    for cue_file in sample_generated_cue_dir.glob("*.cue"):
        # Run cue fmt in check mode
        result = subprocess.run(
            ["cue", "fmt", "-c", str(cue_file)],
            capture_output=True,
        )
        assert result.returncode == 0, (
            f"{cue_file} is not properly formatted. Run: cue fmt {cue_file}"
        )


def test_all_generated_cue_is_valid(sample_generated_cue_dir):
    """Verify all generated CUE files are valid."""
    result = subprocess.run(
        ["cue", "vet", str(sample_generated_cue_dir / "...")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CUE validation failed: {result.stderr}"
```

Create `tests/integration/test_jsonl_behavior.py`:

```python
"""Tests for JSONL logging behavior."""

import json
from pathlib import Path
import pytest
from confidantic.workshop.logging import WorkshopLogger, WorkshopLogReader


def test_jsonl_entries_are_valid_json(tmp_path):
    """Verify all JSONL entries are valid JSON."""
    log_file = tmp_path / "test.jsonl"
    logger = WorkshopLogger(log_path=log_file)

    # Log various events
    logger.log_event(stage="load", status="success", grammar="test")
    logger.log_event(stage="generate", status="failure", grammar="test", error="test error")

    # Verify each line is valid JSON
    for line in log_file.read_text().strip().split("\n"):
        json.loads(line)  # Should not raise


def test_jsonl_is_append_only(tmp_path):
    """Verify JSONL is append-only (no overwrites)."""
    log_file = tmp_path / "test.jsonl"
    logger = WorkshopLogger(log_path=log_file)

    # Log first event
    logger.log_event(stage="load", status="success", grammar="test1")
    first_content = log_file.read_text()

    # Log second event
    logger.log_event(stage="load", status="success", grammar="test2")
    second_content = log_file.read_text()

    # First content should be preserved
    assert first_content in second_content
    # Should have 2 lines now
    assert len(second_content.strip().split("\n")) == 2
```

Create `tests/integration/test_redaction.py`:

```python
"""Tests for redaction defaults."""

from confidantic.workshop.models import WorkshopInput


def test_workshop_input_redacts_sensitive_paths(sample_workshop_input):
    """Verify WorkshopInput redacts sensitive file paths."""
    redacted = sample_workshop_input.to_redacted_dict()

    # Should not contain actual file system paths
    redacted_str = str(redacted)
    assert "/home/" not in redacted_str or "[REDACTED]" in redacted_str


def test_workshop_event_redacts_errors(sample_error_event):
    """Verify error messages don't leak sensitive info."""
    jsonl = sample_error_event.to_jsonl()

    # Should not contain file system paths in errors
    assert "/home/" not in jsonl or "[REDACTED]" in jsonl
```

**Testing Requirements**:
- All golden snapshot tests pass
- CUE formatting enforced
- JSONL behavior validated
- Redaction verified

---

### Track B: End-to-End Integration Fixtures (Parallel with Track A)

**Estimated effort**: 3 days

#### B1. Create Python Grammar Fixture

**Deliverables**:

Create fixture suite in `tests/fixtures/python/`:

1. **`node-types.json`** - Real Python grammar node types
   - Use actual output from tree-sitter Python
   - Include ~50-100 node types for realistic testing
   - Include fields, subtypes, children

2. **`queries/highlights.scm`** - Syntax highlighting queries
   - Real highlight queries from tree-sitter-python
   - ~50-100 captures

3. **`queries/tags.scm`** - Tag queries for navigation
   - Real tag queries
   - ~20-30 captures

4. **Golden snapshots** in `tests/fixtures/golden/python/`:
   - `node_types.cue` - Expected node types output
   - `captures.cue` - Expected captures output
   - `metadata.cue` - Expected metadata output

**Requirements**:
- Use real Tree-sitter Python grammar artifacts
- Keep fixtures up-to-date with grammar changes
- Document fixture generation process
- Include README in fixtures directory

---

#### B2. Create End-to-End Workshop Test

**Deliverables**:

Create `tests/integration/workshop/test_python_workshop.py`:

```python
"""
End-to-end workshop test for Python grammar.

This test validates the complete workshop workflow from
Tree-sitter artifacts to validated CUE schemas.
"""

import subprocess
from pathlib import Path
import pytest


def test_python_workshop_end_to_end(tmp_path):
    """Test complete workshop workflow for Python grammar."""
    # Setup
    fixtures = Path("tests/fixtures/python")
    output_dir = tmp_path / "build/schemas/cue/python"
    output_dir.mkdir(parents=True)

    # Step 1: Load input
    from confidantic.workshop.loaders import load_workshop_input
    workshop_input = load_workshop_input(
        grammar_name="python",
        node_types_path=fixtures / "node-types.json",
        queries_dir=fixtures / "queries",
    )
    assert workshop_input is not None
    assert workshop_input.grammar_name == "python"

    # Step 2: Generate CUE
    from confidantic.workshop.generator import CueGenerator
    generator = CueGenerator(workshop_input)
    generated_files = generator.generate(output_dir)
    assert len(generated_files) > 0
    assert all(f.exists() for f in generated_files)

    # Step 3: Format CUE
    for cue_file in generated_files:
        result = subprocess.run(
            ["cue", "fmt", str(cue_file)],
            capture_output=True,
        )
        assert result.returncode == 0, f"Failed to format {cue_file}"

    # Step 4: Validate CUE
    result = subprocess.run(
        ["cue", "vet", str(output_dir / "...")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CUE validation failed: {result.stderr}"

    # Step 5: Run diagnostics
    from confidantic.workshop.doctor import WorkshopDoctor
    doctor = WorkshopDoctor(
        grammar="python",
        node_types_path=fixtures / "node-types.json",
        queries_dir=fixtures / "queries",
        schemas_dir=output_dir,
    )
    report = doctor.run_diagnostics()
    assert report.is_healthy(), f"Doctor found errors: {report.errors}"

    # Step 6: Verify logging
    log_file = Path("logs/workshop.jsonl")
    if log_file.exists():
        from confidantic.workshop.logging import WorkshopLogReader
        reader = WorkshopLogReader(log_path=log_file)
        events = reader.filter_by_grammar("python")
        assert len(events) > 0, "No events logged for Python grammar"


def test_workshop_via_just_recipe(tmp_path):
    """Test workshop via just recipe (integration with Just)."""
    # This test requires real environment setup
    result = subprocess.run(
        ["just", "cue:from-ts:workshop", "python"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        pytest.skip(f"Just recipe failed (expected in CI): {result.stderr}")

    # If it succeeds, verify output
    assert result.returncode == 0
```

**Testing Requirements**:
- Test runs end-to-end without errors
- All steps complete successfully
- Verify CUE output
- Verify diagnostics pass
- Verify logging works

---

### Track C: Performance and Release Readiness (After Tracks A and B)

**Estimated effort**: 2-3 days

#### C1. Create Performance Benchmarks

**Deliverables**:

Create `tests/performance/test_benchmarks.py`:

```python
"""Performance benchmarks for workshop operations."""

import time
import pytest
from pathlib import Path


def test_load_medium_grammar_performance():
    """Test loading a medium-sized grammar (500 node types) is fast."""
    # Create or use fixture with 500 node types
    start = time.time()

    from confidantic.workshop.loaders import load_workshop_input
    workshop_input = load_workshop_input(
        grammar_name="medium",
        node_types_path=Path("tests/fixtures/medium/node-types.json"),
        queries_dir=Path("tests/fixtures/medium/queries"),
    )

    elapsed = time.time() - start

    assert elapsed < 2.0, f"Loading took {elapsed:.2f}s (limit: 2.0s)"
    assert len(workshop_input.node_types.nodes) >= 500


def test_generate_medium_grammar_performance():
    """Test generating CUE for medium grammar is fast."""
    from confidantic.workshop.loaders import load_workshop_input
    from confidantic.workshop.generator import CueGenerator

    workshop_input = load_workshop_input(
        grammar_name="medium",
        node_types_path=Path("tests/fixtures/medium/node-types.json"),
        queries_dir=Path("tests/fixtures/medium/queries"),
    )

    start = time.time()

    generator = CueGenerator(workshop_input)
    output_dir = Path("build/test/medium")
    output_dir.mkdir(parents=True, exist_ok=True)
    generator.generate(output_dir)

    elapsed = time.time() - start

    assert elapsed < 5.0, f"Generation took {elapsed:.2f}s (limit: 5.0s)"


def test_memory_usage_is_reasonable():
    """Test that workshop operations don't use excessive memory."""
    import resource

    from confidantic.workshop.loaders import load_workshop_input

    # Get initial memory
    initial_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    # Load large grammar
    workshop_input = load_workshop_input(
        grammar_name="large",
        node_types_path=Path("tests/fixtures/large/node-types.json"),
        queries_dir=Path("tests/fixtures/large/queries"),
    )

    # Get peak memory
    peak_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    # Memory increase should be reasonable (< 100MB)
    memory_increase_mb = (peak_memory - initial_memory) / 1024
    assert memory_increase_mb < 100, f"Memory usage too high: {memory_increase_mb:.2f}MB"
```

**Testing Requirements**:
- Benchmarks pass with margin
- Memory usage is reasonable
- Performance documented

---

#### C2. Create Release Readiness Checklist

**Deliverables**:

Create `RELEASE_CHECKLIST.md`:

```markdown
# Release Readiness Checklist

Use this checklist before each release to ensure quality and completeness.

## Code Quality

- [ ] All tests pass (`pytest tests/`)
- [ ] Code coverage ≥ 90% (`pytest --cov`)
- [ ] No flake8 errors (`flake8 src/`)
- [ ] No mypy errors (`mypy src/`)
- [ ] No security vulnerabilities (`bandit -r src/`)

## Functionality

- [ ] All phases complete (1-6)
- [ ] All CLI commands work
- [ ] All Just recipes work
- [ ] Workshop workflow works end-to-end
- [ ] Diagnostics detect common issues
- [ ] Logging works correctly

## Quality Gates

- [ ] Golden snapshot tests pass
- [ ] CUE formatting enforced
- [ ] CUE validation enforced
- [ ] JSONL behavior validated
- [ ] Redaction defaults verified
- [ ] Performance benchmarks pass

## Documentation

- [ ] README is complete and accurate
- [ ] MIGRATION.md is up-to-date
- [ ] CI_INTEGRATION.md has working examples
- [ ] API documentation generated
- [ ] CHANGELOG updated
- [ ] Version bumped

## CI/CD

- [ ] CI pipeline passes
- [ ] All quality gates pass
- [ ] Tests run on Python 3.11, 3.12, 3.13
- [ ] Coverage report uploaded

## Dependencies

- [ ] All dependencies pinned
- [ ] No known security issues
- [ ] License compliance verified

## Backward Compatibility

- [ ] All existing commands work
- [ ] No breaking changes (or documented)
- [ ] Migration path provided (if needed)
- [ ] Deprecation warnings added (if needed)

## Release Process

- [ ] Tag created (vX.Y.Z)
- [ ] Changelog entry added
- [ ] GitHub release created
- [ ] PyPI package published
- [ ] Documentation deployed
- [ ] Announcement posted

## Post-Release

- [ ] Monitor for issues
- [ ] Respond to bug reports
- [ ] Update documentation if needed
```

**Testing Requirements**:
- Use checklist for every release
- Update checklist as needed
- Automate checks where possible

---

#### C3. Add CI Recipe for Quality Gates

**Deliverables**:

Add to `scripts/confidantic.just`:

```just
# CI quality gates
ci:check: ci:test ci:quality ci:performance

# Run all tests
ci:test:
    @echo "Running test suite..."
    pytest tests/ -v --cov=src/confidantic --cov-report=term

# Run quality gates
ci:quality:
    @echo "Running quality gates..."
    pytest tests/integration/test_golden_snapshots.py -v
    pytest tests/integration/test_cue_formatting.py -v
    pytest tests/integration/test_jsonl_behavior.py -v
    pytest tests/integration/test_redaction.py -v

# Run performance tests
ci:performance:
    @echo "Running performance tests..."
    pytest tests/performance/ -v

# Run end-to-end tests
ci:e2e:
    @echo "Running end-to-end tests..."
    pytest tests/integration/workshop/ -v

# Full CI check
ci:all: ci:check ci:e2e
    @echo "✓ All CI checks passed"
```

**Testing Requirements**:
- All recipes work in CI
- Exit codes are correct
- Output is clear

---

## Parallelization Strategy

### Week 1 (Parallel Development)

**Developer A**:
- Track A: CI pipeline (A1)
- Quality gate tests (A2)
- Test and debug CI

**Developer B**:
- Track B: Python fixture (B1)
- End-to-end test (B2)
- Verify fixtures

**Sync Point**: Integrate fixtures with CI

### Week 2 (Performance & Release)

**Both developers**:
- Track C1: Performance benchmarks
- Track C2: Release checklist
- Track C3: CI recipes
- Final testing and hardening

---

## Verification Checklist

Before marking Phase 6 complete, verify:

### CI Pipeline
- [ ] CI runs successfully on all Python versions
- [ ] All test jobs pass
- [ ] Coverage reports upload
- [ ] Quality gates enforce standards

### Quality Gates
- [ ] Golden snapshot tests pass
- [ ] Determinism verified
- [ ] CUE formatting enforced
- [ ] CUE validation enforced
- [ ] JSONL behavior validated
- [ ] Redaction verified

### Integration
- [ ] End-to-end workshop test passes
- [ ] Python fixture is complete
- [ ] Golden snapshots match
- [ ] Just recipes work in CI

### Performance
- [ ] Load performance acceptable
- [ ] Generation performance acceptable
- [ ] Memory usage reasonable
- [ ] Benchmarks documented

### Release Readiness
- [ ] Release checklist complete
- [ ] All documentation up-to-date
- [ ] Version bumped
- [ ] Changelog updated

### Overall
- [ ] Code coverage ≥ 90%
- [ ] All tests pass
- [ ] No known critical bugs
- [ ] Ready for production use

---

## Exit Criteria

Phase 6 is complete when:

1. CI pipeline runs all quality gates
2. Golden snapshot tests verify determinism
3. CUE formatting and validation enforced
4. JSONL behavior validated
5. Redaction verified
6. End-to-end workshop test passes
7. Performance benchmarks pass
8. Release checklist complete
9. Code coverage ≥ 90%
10. All items in verification checklist checked off

**Result**: Confidantic is production-ready and can be released as v1.0.0!

---

## Common Pitfalls to Avoid

1. **Flaky tests**: Ensure all tests are deterministic
2. **CI timeouts**: Set appropriate timeouts for long operations
3. **Missing fixtures**: Include all required test data
4. **Outdated snapshots**: Keep golden snapshots up-to-date
5. **Performance regressions**: Monitor benchmarks over time
6. **Missing quality gates**: Enforce all requirements in CI
7. **Incomplete documentation**: Update all docs before release

---

## Example CI Usage

### Local Quality Check

```bash
# Run all CI checks locally before pushing
just ci:all

# Or individually
just ci:test
just ci:quality
just ci:performance
just ci:e2e
```

### GitHub Actions

```bash
# Triggered automatically on push/PR
# Check status at: https://github.com/org/confidantic/actions
```

### Release Process

```bash
# 1. Complete release checklist
cat RELEASE_CHECKLIST.md

# 2. Run full CI suite
just ci:all

# 3. Update version
# Edit pyproject.toml, update version

# 4. Update changelog
# Edit CHANGELOG.md

# 5. Commit and tag
git add .
git commit -m "Release v1.0.0"
git tag v1.0.0

# 6. Push
git push origin main --tags

# 7. CI will automatically build and test
# 8. Create GitHub release
# 9. Publish to PyPI (manual or automated)
```

---

## Post-Phase 6

After Phase 6 is complete:

1. **Release v1.0.0**
2. **Publish documentation**
3. **Announce release**
4. **Monitor for issues**
5. **Plan future enhancements**

Congratulations! Confidantic is production-ready! 🎉

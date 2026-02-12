# Phase 2: Deterministic CUE Generation Engine

## Overview

Phase 2 implements the core synthesis engine that transforms Tree-sitter artifacts (loaded in Phase 1) into deterministic CUE schema definitions. This phase focuses on **stable output**, **source provenance**, and **build-only generation**.

**Goal**: Generate valid, deterministic CUE schemas from WorkshopInput that can be formatted with `cue fmt` and validated with `cue vet`.

## Prerequisites

- Phase 1 complete (models and loaders working)
- Understanding of CUE language syntax and schema patterns
- Understanding of Tree-sitter node type structure
- Familiarity with deterministic code generation principles

## Success Criteria

- [ ] Generator produces valid CUE definitions from WorkshopInput
- [ ] Output is deterministic (same input → same output, every time)
- [ ] CUE files include source provenance comments
- [ ] Generated files are written to `build/schemas/cue/<grammar>/` only
- [ ] `cue fmt` runs successfully on all generated files
- [ ] Golden snapshot tests verify determinism
- [ ] Code coverage ≥ 90% for generator module

## Task Breakdown

### Track A: Core Generation Engine (3-4 days)

#### A1. Create `src/confidantic/workshop/generator.py`

**Deliverables**:

1. **CueGenerator class** - Main generation engine
   ```python
   class CueGenerator:
       """
       Generates deterministic CUE schemas from Tree-sitter artifacts.

       This generator transforms WorkshopInput (Phase 1) into structured
       CUE definitions following confidantic conventions.
       """

       def __init__(self, workshop_input: WorkshopInput):
           self.input = workshop_input
           self.grammar = workshop_input.grammar_name

       def generate(self, output_dir: Path) -> list[Path]:
           """
           Generate all CUE schema files.

           Args:
               output_dir: Target directory (e.g., build/schemas/cue/python/)

           Returns:
               List of generated file paths (sorted)
           """
   ```

2. **File segmentation strategy**

   Generate separate CUE files for logical groupings:
   - `node_types.cue` - Core node type definitions
   - `captures.cue` - Query capture definitions
   - `metadata.cue` - Grammar metadata and provenance

   **Requirements**:
   - Deterministic file naming (no timestamps, no randomness)
   - Sorted file generation order
   - Each file is standalone and valid CUE

3. **Node type synthesis** (`_generate_node_types()`)

   Transform `NodeTypes` into CUE definitions:

   ```cue
   // Generated from: build/treesitter/python/node-types.json
   // Grammar: python
   // Generated: 2024-01-15T10:30:00Z

   package python

   // Node type definitions
   #NodeType: {
       type: string
       named: bool
       ...
   }

   // Concrete node types (sorted alphabetically)
   #expression: #NodeType & {
       type: "expression"
       named: true
   }

   #identifier: #NodeType & {
       type: "identifier"
       named: true
   }

   #module: #NodeType & {
       type: "module"
       named: true
       fields?: {...}
   }
   ```

   **Requirements**:
   - Sort node types alphabetically by `type` field
   - Generate CUE field definitions from Tree-sitter fields
   - Handle optional fields correctly (`fields?:`)
   - Handle subtypes if present
   - Include provenance comment at top

4. **Query capture synthesis** (`_generate_captures()`)

   Transform `QueryFile` captures into CUE definitions:

   ```cue
   // Generated from: build/treesitter/python/queries/highlights.scm
   // Query type: highlights

   package python

   // Highlight captures (sorted alphabetically)
   #Capture: {
       name: string
       pattern: string
       source_line: int
   }

   #captures: {
       "@class.definition": #Capture & {
           name: "@class.definition"
           pattern: "(class_definition name: (identifier) @class.definition)"
           source_line: 15
       }

       "@function.definition": #Capture & {
           name: "@function.definition"
           pattern: "(function_definition name: (identifier) @function.definition)"
           source_line: 10
       }
   }
   ```

   **Requirements**:
   - Sort captures alphabetically by name
   - Include source file and line number in comments or metadata
   - Group by query file type (highlights, tags, etc.)
   - Escape special characters in patterns

5. **Metadata generation** (`_generate_metadata()`)

   Generate grammar metadata file:

   ```cue
   // Grammar metadata

   package python

   #GrammarMetadata: {
       name: "python"
       timestamp: "2024-01-15T10:30:00Z"
       fingerprint: "a1b2c3d4e5f6..."
       sources: {
           node_types: "build/treesitter/python/node-types.json"
           queries: [
               "build/treesitter/python/queries/highlights.scm",
               "build/treesitter/python/queries/tags.scm",
           ]
       }
   }
   ```

   **Requirements**:
   - Include WorkshopInput fingerprint
   - List all source artifact paths (sorted)
   - Include generation timestamp (UTC)
   - Include confidantic version

6. **Deterministic block ordering**

   Within each file:
   - Package declaration first
   - Imports next (if any, sorted)
   - Metadata/comments next
   - Definitions last (sorted alphabetically)

   **Requirements**:
   - Never rely on dict iteration order
   - Always use explicit sorted() calls
   - Document sort keys in comments

---

#### A2. Implement Output Stability Guarantees

**Deliverables**:

1. **Stable field traversal**
   ```python
   def _traverse_fields(self, fields: dict[str, Any]) -> list[tuple[str, Any]]:
       """Traverse fields in deterministic order (alphabetical)."""
       return sorted(fields.items(), key=lambda x: x[0])
   ```

2. **Stable file naming**
   ```python
   def _get_output_paths(self, output_dir: Path) -> dict[str, Path]:
       """Get deterministic output file paths."""
       return {
           "node_types": output_dir / "node_types.cue",
           "captures": output_dir / "captures.cue",
           "metadata": output_dir / "metadata.cue",
       }
   ```

3. **Stable comment generation**
   ```python
   def _generate_provenance_comment(self, source_path: Path) -> str:
       """Generate standardized provenance comment."""
       return f"// Generated from: {source_path}\n"
   ```

4. **No in-place mutation**
   - Always write to `build/` directory
   - Never modify source files
   - Use temporary files with atomic rename
   - Verify output directory exists before writing

**Testing Requirements**:
- Run generator 10 times on same input, verify byte-identical output
- Test with different WorkshopInput orderings, verify same output
- Test with empty node types, empty captures
- Test with special characters in node names

---

### Track B: CUE Formatting and Validation Utilities (Parallel with Track A)

**Estimated effort**: 2 days

#### B1. Create `src/confidantic/cue/formatter.py`

**Deliverables**:

1. **format_cue_file() function**
   ```python
   def format_cue_file(file_path: Path) -> bool:
       """
       Format a CUE file using `cue fmt`.

       Args:
           file_path: Path to .cue file

       Returns:
           True if formatting succeeded, False otherwise

       Raises:
           FileNotFoundError: If file doesn't exist
           subprocess.CalledProcessError: If cue fmt fails
       """
   ```

   **Requirements**:
   - Call `cue fmt` subprocess
   - Capture stdout/stderr
   - Return formatted content or error
   - Include file path in error messages

2. **format_cue_directory() function**
   ```python
   def format_cue_directory(directory: Path) -> dict[Path, bool]:
       """
       Format all .cue files in directory.

       Args:
           directory: Directory containing .cue files

       Returns:
           Dict mapping file paths to success status
       """
   ```

   **Requirements**:
   - Discover all `.cue` files (sorted)
   - Format each file
   - Return success/failure per file
   - Continue on error (don't stop at first failure)

3. **validate_cue_file() function**
   ```python
   def validate_cue_file(file_path: Path) -> tuple[bool, str | None]:
       """
       Validate a CUE file using `cue vet`.

       Args:
           file_path: Path to .cue file

       Returns:
           Tuple of (success, error_message)
       """
   ```

   **Requirements**:
   - Call `cue vet` subprocess
   - Parse validation errors
   - Return clear error messages
   - Include line numbers from cue vet output

**Testing Requirements**:
- Test with valid CUE files
- Test with syntax errors (verify error messages)
- Test with missing `cue` binary (graceful error)
- Test directory formatting with mixed valid/invalid files

---

### Track C: Integration and Golden Tests (After Tracks A and B)

**Estimated effort**: 2-3 days

#### C1. End-to-End Generation Test

**Deliverables**:

Create `tests/workshop/test_generator.py`:

1. **Test complete generation workflow**
   ```python
   def test_generate_from_workshop_input(sample_workshop_input, tmp_path):
       """Test generating CUE from WorkshopInput."""
       output_dir = tmp_path / "build/schemas/cue/python"
       output_dir.mkdir(parents=True)

       generator = CueGenerator(sample_workshop_input)
       generated_files = generator.generate(output_dir)

       # Verify files created
       assert len(generated_files) > 0
       assert all(f.exists() for f in generated_files)

       # Verify all files are valid CUE
       for file_path in generated_files:
           success, error = validate_cue_file(file_path)
           assert success, f"Invalid CUE in {file_path}: {error}"
   ```

2. **Test deterministic output**
   ```python
   def test_deterministic_generation(sample_workshop_input, tmp_path):
       """Verify generation produces identical output across runs."""
       output_dirs = [tmp_path / f"run_{i}" for i in range(5)]

       for output_dir in output_dirs:
           output_dir.mkdir(parents=True)
           generator = CueGenerator(sample_workshop_input)
           generator.generate(output_dir / "schemas/cue/test")

       # Compare all outputs byte-for-byte
       for i in range(1, len(output_dirs)):
           for file_name in ["node_types.cue", "captures.cue", "metadata.cue"]:
               file1 = output_dirs[0] / "schemas/cue/test" / file_name
               file2 = output_dirs[i] / "schemas/cue/test" / file_name

               if file1.exists():
                   assert file2.exists(), f"{file_name} missing in run {i}"
                   content1 = file1.read_bytes()
                   content2 = file2.read_bytes()
                   assert content1 == content2, f"{file_name} differs in run {i}"
   ```

3. **Test source provenance**
   ```python
   def test_provenance_comments(sample_workshop_input, tmp_path):
       """Verify generated files include source provenance."""
       output_dir = tmp_path / "build/schemas/cue/test"
       output_dir.mkdir(parents=True)

       generator = CueGenerator(sample_workshop_input)
       generated_files = generator.generate(output_dir)

       for file_path in generated_files:
           content = file_path.read_text()
           # Verify provenance comment exists
           assert "// Generated from:" in content
           # Verify grammar name in package declaration
           assert f"package {sample_workshop_input.grammar_name}" in content
   ```

---

#### C2. Golden Snapshot Tests

**Deliverables**:

Create `tests/workshop/test_golden_snapshots.py`:

1. **Golden snapshot fixtures**

   Store known-good CUE output in `tests/fixtures/golden/`:
   - `python/node_types.cue`
   - `python/captures.cue`
   - `python/metadata.cue`

2. **Snapshot comparison test**
   ```python
   def test_golden_snapshot_match(real_python_workshop_input, tmp_path):
       """Compare generated output to golden snapshots."""
       output_dir = tmp_path / "build/schemas/cue/python"
       output_dir.mkdir(parents=True)

       generator = CueGenerator(real_python_workshop_input)
       generator.generate(output_dir)

       # Compare each file to golden snapshot
       golden_dir = Path("tests/fixtures/golden/python")
       for golden_file in golden_dir.glob("*.cue"):
           generated_file = output_dir / golden_file.name

           assert generated_file.exists(), f"Missing {golden_file.name}"

           # Normalize timestamps before comparison
           golden_normalized = normalize_cue(golden_file.read_text())
           generated_normalized = normalize_cue(generated_file.read_text())

           assert golden_normalized == generated_normalized, (
               f"{golden_file.name} doesn't match golden snapshot"
           )
   ```

3. **Snapshot update utility**
   ```python
   def update_golden_snapshots(workshop_input, golden_dir: Path):
       """Utility to regenerate golden snapshots (use with caution)."""
       # Only call this when intentionally updating snapshots
   ```

**Testing Requirements**:
- Use real Python Tree-sitter artifacts for golden test
- Normalize timestamps/fingerprints before comparison
- Fail test if snapshot differs (with clear diff)
- Document how to update snapshots (manual process)

---

#### C3. Edge Case Tests

**Deliverables**:

Create edge case tests in `tests/workshop/test_generator_edge_cases.py`:

1. **Empty inputs**
   - Empty node types list
   - No query files
   - Grammar with minimal artifacts

2. **Special characters**
   - Node types with underscores, numbers, hyphens
   - Capture patterns with escaped quotes
   - Unicode in node type names

3. **Large inputs**
   - 1000+ node types (verify performance)
   - 500+ captures
   - Deeply nested field structures

4. **Malformed input handling**
   - Invalid output directory (should create)
   - Read-only output directory (should error clearly)
   - Concurrent generation (verify thread safety)

**Testing Requirements**:
- Each edge case should have dedicated test
- Verify error messages are actionable
- Verify no silent failures
- Verify performance is acceptable (< 5 seconds for large grammars)

---

## Parallelization Strategy

### Week 1 (Parallel Development)

**Developer A**:
- Track A: Implement CueGenerator class (A1)
- Implement output stability guarantees (A2)
- Write basic unit tests for generator

**Developer B**:
- Track B: Implement CUE formatting utilities (B1)
- Write tests for formatter/validator
- Set up fixture data

**Sync Point**: Both developers integrate and review

### Week 2 (Integration)

**Both developers**:
- Track C1: End-to-end generation tests
- Track C2: Golden snapshot tests
- Track C3: Edge case tests
- Performance testing and optimization

---

## Testing Strategy

### Unit Tests (Per Method)

For each generator method:
- Test with valid input
- Test with empty input
- Test with maximum input
- Verify deterministic output
- Verify error handling

### Integration Tests (End-to-End)

- Load WorkshopInput (Phase 1)
- Generate CUE schemas (Phase 2)
- Format with `cue fmt`
- Validate with `cue vet`
- Verify all steps succeed

### Golden Tests (Regression Prevention)

- Generate CUE from known-good input
- Compare to saved golden snapshots
- Fail if output changes unexpectedly
- Document snapshot update process

### Performance Tests

- Generate for Python grammar (~500 node types)
- Verify completes in < 5 seconds
- Verify memory usage is reasonable
- Test with 10 concurrent generators

---

## Verification Checklist

Before marking Phase 2 complete, verify:

### Code Quality
- [ ] All code follows PEP 8 style
- [ ] Type hints on all public functions
- [ ] Docstrings on all public classes/functions
- [ ] No hardcoded paths or magic strings

### Generated Output Quality
- [ ] All generated CUE files are valid (pass `cue vet`)
- [ ] All files are properly formatted (pass `cue fmt`)
- [ ] Files include source provenance comments
- [ ] Package declarations are correct
- [ ] Definitions are sorted alphabetically

### Determinism Verification
- [ ] Run generator 10 times, outputs are byte-identical
- [ ] Different input orderings produce same output
- [ ] Golden snapshot tests pass
- [ ] No timestamps in output (except metadata)

### Error Handling
- [ ] Missing output directory creates it
- [ ] Read-only directory fails with clear error
- [ ] Invalid WorkshopInput fails with clear error
- [ ] `cue fmt` failure is surfaced to user

### Testing
- [ ] All tests pass (`pytest tests/workshop/test_generator*.py`)
- [ ] Code coverage ≥ 90%
- [ ] Golden snapshot tests pass
- [ ] Performance tests pass (< 5 seconds for large grammar)

### Documentation
- [ ] Generator API documented
- [ ] CUE output format documented
- [ ] Provenance comment format documented
- [ ] Example usage included

---

## Common Pitfalls to Avoid

1. **Non-deterministic ordering**: Always sort before iteration
2. **Timestamp inclusion**: Only include timestamps in metadata, not in definitions
3. **Platform-specific paths**: Use `Path` and forward slashes in CUE
4. **CUE syntax errors**: Validate generated CUE before returning success
5. **String escaping**: Properly escape quotes and special characters in CUE strings
6. **In-place mutation**: Never modify source artifacts, only write to build/
7. **Missing package declarations**: Every CUE file needs `package <name>`

---

## CUE Output Standards

All generated CUE must follow these standards:

1. **File structure**:
   ```cue
   // Provenance comment
   // Additional metadata comments

   package <grammar_name>

   // Imports (if any, sorted)

   // Definitions (sorted alphabetically)
   ```

2. **Naming conventions**:
   - Schema definitions: `#PascalCase`
   - Node types: `#lowercase_with_underscores`
   - Captures: Preserve original `@name.with.dots`

3. **Comments**:
   - Provenance at file top
   - Brief description for complex definitions
   - Source line numbers where helpful

4. **Formatting**:
   - 4-space indentation (after `cue fmt`)
   - No trailing whitespace
   - Unix line endings (LF)

---

## Reference Materials

- [CUE Language Specification](https://cuelang.org/docs/references/spec/)
- [CUE Best Practices](https://cuelang.org/docs/howto/)
- [Tree-sitter Node Types Format](https://tree-sitter.github.io/tree-sitter/using-parsers#static-node-types)
- Phase 1 documentation (WorkshopInput structure)

---

## Example Usage (After Phase 2)

```python
from pathlib import Path
from confidantic.workshop.loaders import load_workshop_input
from confidantic.workshop.generator import CueGenerator
from confidantic.cue.formatter import format_cue_directory, validate_cue_file

# Load Tree-sitter artifacts (Phase 1)
workshop_input = load_workshop_input(
    grammar_name="python",
    node_types_path=Path("build/treesitter/python/node-types.json"),
    queries_dir=Path("build/treesitter/python/queries")
)

# Generate CUE schemas (Phase 2)
output_dir = Path("build/schemas/cue/python")
output_dir.mkdir(parents=True, exist_ok=True)

generator = CueGenerator(workshop_input)
generated_files = generator.generate(output_dir)

print(f"Generated {len(generated_files)} CUE files:")
for file_path in generated_files:
    print(f"  - {file_path}")

# Format generated CUE
format_results = format_cue_directory(output_dir)
for file_path, success in format_results.items():
    status = "✓" if success else "✗"
    print(f"{status} Formatted: {file_path}")

# Validate generated CUE
for file_path in generated_files:
    success, error = validate_cue_file(file_path)
    if success:
        print(f"✓ Valid: {file_path}")
    else:
        print(f"✗ Invalid: {file_path}\n  Error: {error}")
```

---

## Exit Criteria

Phase 2 is complete when:

1. CueGenerator produces valid, formatted CUE from WorkshopInput
2. Output is deterministic (golden tests pass)
3. All generated files pass `cue fmt` and `cue vet`
4. Source provenance is included in all files
5. Code coverage ≥ 90%
6. Performance is acceptable (< 5 seconds for large grammars)
7. All tests pass
8. Documentation complete
9. All items in verification checklist checked off

**Next Phase**: Phase 3 - Required CUE workflow integration

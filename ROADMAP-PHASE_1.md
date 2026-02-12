# Phase 1: Workshop Input Model and Ingestion

## Overview

Phase 1 establishes the foundation for the Tree-sitter-to-CUE workshop by creating typed models and deterministic loaders for ingesting Tree-sitter artifacts. This phase focuses on **input validation**, **deterministic ordering**, and **safe error handling**.

**Goal**: Reliably ingest and validate Tree-sitter artifacts (`node-types.json` and `.scm` query files) with deterministic behavior and strict error reporting.

## Prerequisites

- Phase 0 complete (scope lock confirmed)
- Development environment set up via devenv
- Python 3.11+ installed
- Familiarity with Pydantic models
- Understanding of Tree-sitter `node-types.json` and `.scm` query file formats

## Success Criteria

- [ ] All Tree-sitter artifact types have typed Pydantic models
- [ ] Loaders produce stable, deterministic output regardless of filesystem order
- [ ] Parse errors include file path and line/column context
- [ ] JSONL event logging model is defined and usable
- [ ] All tests pass (malformed, partial, and missing input scenarios)
- [ ] Code coverage ≥ 90% for models and loaders

## Task Breakdown

### Track A: Data Models (Can be done in parallel with Track B)

**Estimated effort**: 2-3 days

#### A1. Create `src/confidantic/workshop/models.py`

Create typed Pydantic models for all Tree-sitter artifacts.

**Deliverables**:

1. **NodeType Model** - Represents a single node type from `node-types.json`
   ```python
   class NodeType(BaseModel):
       type: str
       named: bool
       fields: dict[str, Any] = {}
       children: dict[str, Any] | None = None
       subtypes: list[dict[str, Any]] | None = None
   ```

2. **NodeTypes Model** - Container for all node types
   ```python
   class NodeTypes(BaseModel):
       nodes: list[NodeType]

       @field_validator('nodes')
       @classmethod
       def ensure_deterministic_order(cls, v):
           # Sort by type name for deterministic processing
           return sorted(v, key=lambda n: n.type)
   ```

3. **QueryCapture Model** - Represents a parsed capture from `.scm` files
   ```python
   class QueryCapture(BaseModel):
       name: str  # e.g., "@function.definition"
       pattern: str  # S-expression pattern
       source_file: Path
       line_number: int

       model_config = ConfigDict(frozen=True)  # Immutable
   ```

4. **QueryFile Model** - Container for captures from a single `.scm` file
   ```python
   class QueryFile(BaseModel):
       file_path: Path
       query_type: Literal["highlights", "tags", "injections", "locals"]
       captures: list[QueryCapture]

       @field_validator('captures')
       @classmethod
       def sort_captures(cls, v):
           # Deterministic ordering: by name, then line number
           return sorted(v, key=lambda c: (c.name, c.line_number))
   ```

5. **WorkshopInput Model** - Normalized intermediate representation (IR)
   ```python
   class WorkshopInput(BaseModel):
       """Normalized IR combining node types and query captures."""
       grammar_name: str
       node_types: NodeTypes
       query_files: list[QueryFile]
       timestamp: datetime
       source_paths: dict[str, Path]  # artifact_type -> source_path

       def fingerprint(self) -> str:
           """Generate deterministic fingerprint for this input."""
           # Hash sorted combination of node types and captures
   ```

6. **WorkshopEvent Model** - JSONL log event structure
   ```python
   class WorkshopEvent(BaseModel):
       """Single event for append-only workshop.jsonl logs."""
       timestamp: datetime
       stage: Literal["load", "generate", "fmt", "vet", "test", "doctor"]
       status: Literal["started", "success", "failure"]
       grammar: str | None = None
       artifact_paths: list[Path] = []
       error: str | None = None
       metadata: dict[str, Any] = {}

       def to_jsonl(self) -> str:
           """Serialize to JSONL format with redaction."""
           return self.model_dump_json(exclude_none=True)
   ```

**Testing Requirements**:
- Test model validation with valid Tree-sitter data
- Test deterministic ordering (run multiple times, verify same order)
- Test immutability of QueryCapture
- Test fingerprint stability
- Test JSONL serialization and deserialization

---

#### A2. Add Model Validation and Edge Cases

**Deliverables**:

1. Add validators for:
   - Non-empty grammar names
   - Valid file paths (must exist)
   - Capture name format (must start with `@`)
   - Timestamp UTC enforcement

2. Handle edge cases:
   - Empty node types array (should error)
   - Duplicate node type names (should warn but allow)
   - Capture patterns with escaped quotes
   - Unicode in node type names

**Testing Requirements**:
- Test each validator with valid and invalid inputs
- Test edge cases explicitly
- Verify error messages are clear and actionable

---

### Track B: Deterministic Loaders (Can be done in parallel with Track A)

**Estimated effort**: 3-4 days

#### B1. Create `src/confidantic/workshop/loaders.py`

Implement deterministic loaders for Tree-sitter artifacts.

**Deliverables**:

1. **load_node_types() function**
   ```python
   def load_node_types(path: Path) -> NodeTypes:
       """
       Load and parse node-types.json with strict validation.

       Args:
           path: Path to node-types.json file

       Returns:
           Validated NodeTypes model

       Raises:
           FileNotFoundError: If path doesn't exist
           ValidationError: If JSON is invalid or malformed
       """
   ```

   **Requirements**:
   - Read JSON with UTF-8 encoding
   - Parse into NodeTypes model
   - Include file path in error messages
   - Log warnings for unknown fields (strict mode)

2. **load_query_file() function**
   ```python
   def load_query_file(
       path: Path,
       query_type: Literal["highlights", "tags", "injections", "locals"]
   ) -> QueryFile:
       """
       Parse a Tree-sitter .scm query file into structured captures.

       Args:
           path: Path to .scm file
           query_type: Type of query file

       Returns:
           Validated QueryFile model

       Raises:
           FileNotFoundError: If path doesn't exist
           ParseError: If S-expression syntax is invalid, includes line/col
       """
   ```

   **Requirements**:
   - Parse S-expressions (you may use tree-sitter bindings)
   - Extract capture names (strings starting with `@`)
   - Track line numbers for each capture
   - Handle multi-line patterns correctly
   - Detect syntax errors with context

3. **discover_query_files() function**
   ```python
   def discover_query_files(
       queries_dir: Path,
       required: list[str] | None = None
   ) -> list[Path]:
       """
       Discover .scm query files with deterministic ordering.

       Args:
           queries_dir: Directory containing query files
           required: Optional list of required filenames (e.g., ["highlights.scm"])

       Returns:
           Sorted list of .scm file paths

       Raises:
           FileNotFoundError: If required files are missing
       """
   ```

   **Requirements**:
   - Scan directory for `*.scm` files
   - **Sort alphabetically for deterministic order**
   - Check for required files if specified
   - Ignore hidden files (starting with `.`)

4. **load_workshop_input() function** (high-level orchestrator)
   ```python
   def load_workshop_input(
       grammar_name: str,
       node_types_path: Path,
       queries_dir: Path
   ) -> WorkshopInput:
       """
       Load complete workshop input for a grammar.

       This is the primary entry point for ingestion.

       Args:
           grammar_name: Name of the grammar (e.g., "python", "rust")
           node_types_path: Path to node-types.json
           queries_dir: Directory containing query .scm files

       Returns:
           Complete WorkshopInput with all artifacts loaded
       """
   ```

   **Requirements**:
   - Load node types
   - Discover and load all query files
   - Combine into WorkshopInput
   - Set timestamp to UTC now
   - Track source paths
   - Return deterministically ordered result

**Testing Requirements**:
- Test with valid Tree-sitter artifacts from a real grammar (e.g., Python)
- Test missing files (should error with clear message)
- Test malformed JSON (should error with file + line)
- Test malformed S-expressions (should error with file + line + column)
- Test partial query files (missing captures)
- Test deterministic ordering (run 10 times, compare results)
- Test empty directories
- Test permission errors

---

#### B2. Add JSONL Event Logging Utilities

**Deliverables**:

1. **log_workshop_event() function**
   ```python
   def log_workshop_event(
       event: WorkshopEvent,
       log_path: Path = Path("logs/workshop.jsonl")
   ) -> None:
       """
       Append a workshop event to JSONL log.

       Args:
           event: WorkshopEvent to log
           log_path: Path to JSONL log file (created if missing)
       """
   ```

   **Requirements**:
   - Create parent directories if needed
   - Append one line per event (no overwrites)
   - Handle concurrent writes safely (use file locking)
   - Ensure UTF-8 encoding

2. **load_workshop_events() function**
   ```python
   def load_workshop_events(
       log_path: Path = Path("logs/workshop.jsonl")
   ) -> list[WorkshopEvent]:
       """
       Load all events from a workshop JSONL log.

       Args:
           log_path: Path to JSONL log file

       Returns:
           List of WorkshopEvent objects in chronological order
       """
   ```

   **Requirements**:
   - Read line-by-line
   - Parse each line as WorkshopEvent
   - Skip blank lines
   - Report line numbers for invalid entries
   - Return in order (chronological)

**Testing Requirements**:
- Test appending multiple events
- Test loading events back
- Test concurrent writes (use threading)
- Test malformed JSONL lines (should report line number)
- Test empty log file
- Test missing log file (should create)

---

### Track C: Integration and Testing (After Tracks A and B)

**Estimated effort**: 2 days

#### C1. Write Comprehensive Tests

Create test files:
- `tests/workshop/test_models.py`
- `tests/workshop/test_loaders.py`
- `tests/workshop/test_integration.py`

**Test Categories**:

1. **Model Tests** (`test_models.py`)
   - Valid model creation
   - Validation errors
   - Deterministic ordering
   - Fingerprint stability
   - JSONL serialization

2. **Loader Tests** (`test_loaders.py`)
   - Loading valid artifacts
   - Error handling (missing files, malformed data)
   - Deterministic discovery
   - S-expression parsing edge cases

3. **Integration Tests** (`test_integration.py`)
   - End-to-end: load real Tree-sitter grammar artifacts
   - Verify complete WorkshopInput creation
   - Test with Python grammar (include fixture data)
   - Test JSONL logging full workflow

**Fixture Requirements**:
- Include sample `node-types.json` files
- Include sample `.scm` query files
- Include malformed versions for error testing
- Use real Tree-sitter Python grammar as golden example

#### C2. Add Golden Test for Determinism

Create `tests/workshop/test_determinism.py`:

```python
def test_load_determinism():
    """Verify loading produces identical results across runs."""
    results = []
    for _ in range(10):
        workshop_input = load_workshop_input(
            grammar_name="python",
            node_types_path=Path("tests/fixtures/python/node-types.json"),
            queries_dir=Path("tests/fixtures/python/queries")
        )
        results.append(workshop_input.fingerprint())

    # All fingerprints must be identical
    assert len(set(results)) == 1, "Non-deterministic loading detected!"
```

---

## Parallelization Strategy

To maximize development velocity, structure work as follows:

### Week 1 (Parallel Development)

**Developer A**:
- Track A: Create models.py (A1, A2)
- Write model tests

**Developer B**:
- Track B: Create loaders.py (B1, B2)
- Write loader tests

**Sync Point**: Both developers review each other's code

### Week 2 (Integration)

**Both developers**:
- Track C: Integration tests
- Golden tests for determinism
- Fix any issues discovered
- Code review and refinement

---

## Testing Strategy

### Unit Tests (Per Function/Model)

- **Test valid inputs**: Verify correct parsing and model creation
- **Test invalid inputs**: Verify clear error messages with context
- **Test edge cases**: Empty files, unicode, special characters
- **Test determinism**: Run operations multiple times, verify identical results

### Integration Tests (End-to-End)

- **Real grammar test**: Use Python Tree-sitter grammar as fixture
- **Load complete WorkshopInput**: Verify all artifacts combine correctly
- **JSONL workflow**: Create events, log them, load them back
- **Error propagation**: Verify errors bubble up with context

### Golden Tests (Determinism)

- **Fingerprint stability**: Load same input 10 times, verify same fingerprint
- **Sort order stability**: Verify node types and captures always in same order
- **File discovery stability**: Run discovery multiple times, verify same order

### Error Handling Tests

Create fixtures for:
- Missing `node-types.json`
- Malformed JSON (syntax error at line X)
- Invalid S-expression in `.scm` (syntax error at line X, column Y)
- Missing required query files
- Empty node types array
- Duplicate captures

**For each error case**:
- Verify exception is raised
- Verify error message includes file path
- Verify error message includes line/column if applicable
- Verify error message is actionable (tells user how to fix)

---

## Verification Checklist

Before marking Phase 1 complete, verify:

### Code Quality
- [ ] All Python code follows PEP 8 style
- [ ] Type hints on all public functions
- [ ] Docstrings on all public classes and functions (Google style)
- [ ] No unused imports or variables

### Testing
- [ ] All tests pass (`pytest tests/`)
- [ ] Code coverage ≥ 90% (`pytest --cov=src/confidantic/workshop`)
- [ ] Golden determinism tests pass (10 runs, same output)
- [ ] Error tests verify file/line context in messages

### Determinism
- [ ] Node types always sorted by `type` field
- [ ] Query captures sorted by name, then line number
- [ ] File discovery sorted alphabetically
- [ ] Fingerprints stable across runs

### Error Handling
- [ ] All file operations handle missing files
- [ ] Parse errors include file path + line + column
- [ ] Validation errors include field name and expected format
- [ ] No silent failures (every error is raised or logged)

### Documentation
- [ ] README updated with Phase 1 completion
- [ ] API documentation generated (if using Sphinx/MkDocs)
- [ ] Example usage documented in docstrings

---

## Common Pitfalls to Avoid

1. **Non-deterministic ordering**: Always sort collections explicitly
2. **Silent failures**: Never catch exceptions without re-raising or logging
3. **Filesystem dependency**: Don't rely on OS-specific file ordering
4. **Unicode handling**: Always use UTF-8 encoding explicitly
5. **Timezone issues**: Always use UTC for timestamps
6. **Mutable models**: Use `frozen=True` for immutable models
7. **Missing context in errors**: Always include file path and line numbers

---

## Reference Materials

- [Tree-sitter node-types.json format](https://tree-sitter.github.io/tree-sitter/using-parsers#static-node-types)
- [Tree-sitter query syntax](https://tree-sitter.github.io/tree-sitter/using-parsers#query-syntax)
- [Pydantic models documentation](https://docs.pydantic.dev/latest/concepts/models/)
- [JSONL specification](http://jsonlines.org/)

---

## Example Usage (After Phase 1)

```python
from confidantic.workshop.loaders import load_workshop_input
from confidantic.workshop.models import WorkshopEvent
from pathlib import Path

# Load Tree-sitter artifacts for Python grammar
workshop_input = load_workshop_input(
    grammar_name="python",
    node_types_path=Path("build/treesitter/python/node-types.json"),
    queries_dir=Path("build/treesitter/python/queries")
)

# Verify deterministic fingerprint
print(f"Input fingerprint: {workshop_input.fingerprint()}")

# Log the load event
event = WorkshopEvent(
    timestamp=datetime.now(timezone.utc),
    stage="load",
    status="success",
    grammar="python",
    artifact_paths=[
        workshop_input.source_paths["node_types"],
        *[qf.file_path for qf in workshop_input.query_files]
    ]
)

from confidantic.workshop.loaders import log_workshop_event
log_workshop_event(event)
```

---

## Exit Criteria

Phase 1 is complete when:

1. All deliverables exist and pass tests
2. Code coverage ≥ 90%
3. Determinism verified with golden tests
4. Error handling includes file/line context
5. Documentation complete
6. Code reviewed and approved
7. All items in verification checklist checked off

**Next Phase**: Phase 2 - Deterministic CUE generation engine

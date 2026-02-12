# Phase 4: Doctoring, Diagnostics, and Provenance

## Overview

Phase 4 adds comprehensive diagnostics, health checking, and provenance tracking to the workshop workflow. This phase focuses on **observability**, **debugging support**, and **audit trails** through append-only JSONL logging and diagnostic tooling.

**Goal**: Provide developers with clear diagnostics when things go wrong and maintain a complete audit trail of all workshop operations.

## Prerequisites

- Phase 1 complete (models and loaders)
- Phase 2 complete (generator)
- Phase 3 complete (workflow integration)
- Understanding of structured logging (JSONL)
- Familiarity with diagnostics and health checks

## Success Criteria

- [ ] Doctor checks identify all common workshop issues
- [ ] All workshop operations log to `logs/workshop.jsonl`
- [ ] JSONL logs are parseable and queryable with `jq`
- [ ] Diagnostic output is clear and actionable
- [ ] Timing information is captured for performance analysis
- [ ] Agent/session metadata support is included
- [ ] Code coverage ≥ 90% for doctor and logging modules

## Task Breakdown

### Track A: Diagnostic Engine (3-4 days)

#### A1. Create `src/confidantic/workshop/doctor.py`

**Deliverables**:

1. **WorkshopDoctor class** - Main diagnostic engine
   ```python
   class WorkshopDoctor:
       """
       Diagnostic engine for Tree-sitter workshop artifacts and generated CUE.

       Performs health checks and reports issues with actionable messages.
       """

       def __init__(
           self,
           grammar: str,
           node_types_path: Path,
           queries_dir: Path,
           schemas_dir: Path | None = None
       ):
           self.grammar = grammar
           self.node_types_path = node_types_path
           self.queries_dir = queries_dir
           self.schemas_dir = schemas_dir
           self.issues: list[DiagnosticIssue] = []
           self.warnings: list[DiagnosticWarning] = []

       def run_diagnostics(self) -> DiagnosticReport:
           """
           Run all diagnostic checks.

           Returns:
               DiagnosticReport with issues, warnings, and recommendations
           """
   ```

2. **DiagnosticIssue model** - Represents a diagnostic issue
   ```python
   class DiagnosticIssue(BaseModel):
       """A diagnostic issue found during doctor checks."""
       severity: Literal["error", "warning", "info"]
       category: str  # e.g., "missing_artifact", "unmapped_capture"
       message: str
       file_path: Path | None = None
       line_number: int | None = None
       suggestion: str | None = None

       def format(self) -> str:
           """Format issue for display."""
   ```

3. **DiagnosticReport model** - Complete diagnostic report
   ```python
   class DiagnosticReport(BaseModel):
       """Complete diagnostic report from doctor run."""
       grammar: str
       timestamp: datetime
       errors: list[DiagnosticIssue]
       warnings: list[DiagnosticIssue]
       info: list[DiagnosticIssue]
       checks_run: int
       issues_found: int

       def is_healthy(self) -> bool:
           """True if no errors found."""
           return len(self.errors) == 0

       def format_summary(self) -> str:
           """Format report summary for display."""
   ```

4. **Diagnostic check: Missing artifacts** (`_check_missing_artifacts()`)
   ```python
   def _check_missing_artifacts(self) -> None:
       """
       Check for missing or incomplete Tree-sitter artifacts.

       Checks:
       - node-types.json exists and is readable
       - Queries directory exists
       - Required query files present (highlights.scm at minimum)
       - Query files are readable
       """
   ```

   **Requirements**:
   - Check file existence
   - Check file readability (permissions)
   - Verify required query files
   - Report specific missing files with paths

5. **Diagnostic check: Unknown/unmapped captures** (`_check_unmapped_captures()`)
   ```python
   def _check_unmapped_captures(self) -> None:
       """
       Identify captures in query files that don't map to known node types.

       This helps find typos or mismatches between queries and node types.
       """
   ```

   **Requirements**:
   - Load all query captures
   - Load all node types
   - Find captures that reference unknown node types
   - Report file + line number for each issue
   - Suggest possible matches (fuzzy matching)

6. **Diagnostic check: Orphaned node references** (`_check_orphaned_nodes()`)
   ```python
   def _check_orphaned_nodes(self) -> None:
       """
       Find node types that are never referenced in queries.

       This can indicate incomplete query coverage or unused nodes.
       """
   ```

   **Requirements**:
   - Build set of all node types
   - Build set of all referenced nodes from queries
   - Find nodes never referenced
   - Report as info (not error - might be intentional)

7. **Diagnostic check: Deterministic diff warnings** (`_check_determinism()`)
   ```python
   def _check_determinism(self) -> None:
       """
       Check for potential non-determinism in generated CUE.

       Checks:
       - Files are sorted
       - Definitions are sorted
       - No timestamps in definitions
       - No random identifiers
       """
   ```

   **Requirements**:
   - Read generated CUE files if schemas_dir provided
   - Check definition ordering
   - Check for timestamp strings
   - Check for UUIDs or random strings
   - Warn if potential issues found

8. **Diagnostic check: CUE validity** (`_check_cue_validity()`)
   ```python
   def _check_cue_validity(self) -> None:
       """
       Verify generated CUE files are syntactically valid.

       Uses cue vet to check validity.
       """
   ```

   **Requirements**:
   - Run cue vet on schemas_dir if provided
   - Parse cue vet output
   - Report syntax errors with file + line
   - Skip if cue not available (warning only)

9. **Diagnostic check: Performance metrics** (`_check_performance()`)
   ```python
   def _check_performance(self) -> None:
       """
       Check for potential performance issues.

       Checks:
       - Number of node types (warn if > 1000)
       - Number of captures (warn if > 500)
       - File sizes (warn if .cue files > 1MB)
       """
   ```

   **Requirements**:
   - Count node types
   - Count captures
   - Check file sizes
   - Warn if thresholds exceeded
   - Provide optimization suggestions

**Testing Requirements**:
- Test each diagnostic check individually
- Test with valid artifacts (no issues)
- Test with missing files
- Test with unmapped captures
- Test with orphaned nodes
- Test with non-deterministic CUE
- Verify all error messages are actionable

---

#### A2. Implement Rich Diagnostic Output

**Deliverables**:

1. **format_diagnostic_report() function**
   ```python
   def format_diagnostic_report(
       report: DiagnosticReport,
       use_color: bool = True
   ) -> str:
       """
       Format diagnostic report for terminal display.

       Uses rich formatting for better readability.

       Args:
           report: DiagnosticReport to format
           use_color: Whether to use ANSI color codes

       Returns:
           Formatted report string
       """
   ```

   **Requirements**:
   - Use rich tables for issue lists
   - Color-code by severity (red=error, yellow=warning, blue=info)
   - Include file paths and line numbers
   - Show suggestions inline
   - Include summary at bottom

2. **export_diagnostic_report() function**
   ```python
   def export_diagnostic_report(
       report: DiagnosticReport,
       output_path: Path,
       format: Literal["json", "jsonl", "markdown"] = "json"
   ) -> None:
       """
       Export diagnostic report to file.

       Args:
           report: DiagnosticReport to export
           output_path: Where to write report
           format: Output format
       """
   ```

   **Requirements**:
   - Support JSON format (pretty-printed)
   - Support JSONL format (one line)
   - Support Markdown format (for documentation)
   - Include all details
   - Make output machine-parseable

**Testing Requirements**:
- Test formatting with various report types
- Test with/without color
- Test export in all formats
- Verify parseable output

---

### Track B: Provenance Logging System (Parallel with Track A)

**Estimated effort**: 3 days

#### B1. Create `src/confidantic/workshop/logging.py`

**Deliverables**:

1. **WorkshopLogger class** - Structured JSONL logger
   ```python
   class WorkshopLogger:
       """
       Append-only JSONL logger for workshop operations.

       Maintains audit trail of all workshop activities with timing
       and metadata.
       """

       def __init__(self, log_path: Path = Path("logs/workshop.jsonl")):
           self.log_path = log_path
           self._ensure_log_directory()

       def log_event(
           self,
           stage: str,
           status: str,
           grammar: str | None = None,
           artifact_paths: list[Path] | None = None,
           error: str | None = None,
           metadata: dict[str, Any] | None = None,
           duration_ms: float | None = None
       ) -> None:
           """Log a workshop event to JSONL."""

       def log_stage_start(self, stage: str, grammar: str) -> float:
           """Log stage start and return timestamp for duration calculation."""

       def log_stage_end(
           self,
           stage: str,
           grammar: str,
           start_time: float,
           success: bool,
           error: str | None = None
       ) -> None:
           """Log stage end with duration."""
   ```

2. **WorkshopEvent model** (extend from Phase 1)
   ```python
   class WorkshopEvent(BaseModel):
       """Single event in workshop.jsonl log."""
       timestamp: datetime
       stage: Literal["load", "generate", "fmt", "vet", "test", "doctor"]
       status: Literal["started", "success", "failure"]
       grammar: str | None = None
       artifact_paths: list[str] = []  # Stringified paths
       error: str | None = None
       duration_ms: float | None = None
       metadata: dict[str, Any] = {}

       # Optional agent/session tracking
       agent_id: str | None = None
       session_id: str | None = None
       user_id: str | None = None

       def to_jsonl(self) -> str:
           """Serialize to JSONL format (one line)."""
           return self.model_dump_json(exclude_none=True)

       @classmethod
       def from_jsonl(cls, line: str) -> "WorkshopEvent":
           """Parse from JSONL line."""
           return cls.model_validate_json(line)
   ```

3. **WorkshopLogReader class** - Query and analyze logs
   ```python
   class WorkshopLogReader:
       """
       Read and analyze workshop JSONL logs.

       Provides querying and analysis capabilities.
       """

       def __init__(self, log_path: Path = Path("logs/workshop.jsonl")):
           self.log_path = log_path

       def read_all(self) -> list[WorkshopEvent]:
           """Read all events from log."""

       def filter_by_grammar(self, grammar: str) -> list[WorkshopEvent]:
           """Get all events for a specific grammar."""

       def filter_by_stage(self, stage: str) -> list[WorkshopEvent]:
           """Get all events for a specific stage."""

       def filter_by_status(self, status: str) -> list[WorkshopEvent]:
           """Get all events with a specific status."""

       def get_failures(self) -> list[WorkshopEvent]:
           """Get all failure events."""

       def get_recent(self, limit: int = 10) -> list[WorkshopEvent]:
           """Get most recent N events."""

       def calculate_stats(self) -> dict[str, Any]:
           """Calculate statistics from logs."""
   ```

4. **Concurrent logging safety**
   ```python
   import fcntl

   def _safe_append(self, line: str) -> None:
       """
       Safely append line to JSONL log with file locking.

       Ensures concurrent writes don't corrupt log.
       """
       with open(self.log_path, "a") as f:
           fcntl.flock(f.fileno(), fcntl.LOCK_EX)
           try:
               f.write(line + "\n")
               f.flush()
           finally:
               fcntl.flock(f.fileno(), fcntl.LOCK_UN)
   ```

   **Requirements**:
   - Use file locking for thread safety
   - Handle permission errors gracefully
   - Create parent directories if needed
   - Ensure UTF-8 encoding

**Testing Requirements**:
- Test logging single event
- Test logging multiple events
- Test concurrent writes (threading)
- Test reading and filtering
- Test with malformed JSONL (skip bad lines)
- Test statistics calculation

---

#### B2. Integration with Workflow Stages

**Deliverables**:

Update existing workflow stages to use WorkshopLogger:

1. **Update Phase 1 loaders** - Log load events
   ```python
   def load_workshop_input(...) -> WorkshopInput:
       logger = WorkshopLogger()
       start = logger.log_stage_start("load", grammar_name)
       try:
           # ... existing load logic ...
           logger.log_stage_end("load", grammar_name, start, success=True)
           return workshop_input
       except Exception as e:
           logger.log_stage_end("load", grammar_name, start, success=False, error=str(e))
           raise
   ```

2. **Update Phase 2 generator** - Log generate events
3. **Update Phase 3 formatter** - Log fmt events
4. **Update Phase 3 validator** - Log vet events
5. **Update Phase 4 doctor** - Log doctor events

**Requirements**:
- Wrap each major operation
- Log start and end
- Capture timing
- Include error details on failure
- Don't fail workflow if logging fails (log errors, continue)

**Testing Requirements**:
- Verify all stages log events
- Verify timing is captured
- Verify errors are logged
- Verify log doesn't break on write failure

---

### Track C: CLI and Documentation (After Tracks A and B)

**Estimated effort**: 2 days

#### C1. Update CLI Commands

**Deliverables**:

1. **Implement `confidantic workshop doctor` command** (from Phase 3)
   ```python
   @app.command()
   def doctor(
       grammar: str,
       node_types: Path,
       queries_dir: Path,
       schemas_dir: Path | None = None,
       format: Literal["terminal", "json", "markdown"] = "terminal",
       output: Path | None = None
   ) -> None:
       """
       Run diagnostics on workshop artifacts.

       Args:
           grammar: Grammar name
           node_types: Path to node-types.json
           queries_dir: Directory with .scm files
           schemas_dir: Optional directory with generated CUE
           format: Output format (terminal, json, markdown)
           output: Optional file to write report
       """
       doc = WorkshopDoctor(grammar, node_types, queries_dir, schemas_dir)
       report = doc.run_diagnostics()

       if format == "terminal":
           print(format_diagnostic_report(report))
       elif output:
           export_diagnostic_report(report, output, format)

       # Exit non-zero if errors found
       sys.exit(0 if report.is_healthy() else 1)
   ```

2. **Add `confidantic logs` command group**
   ```python
   @logs_app.command()
   def show(
       limit: int = 20,
       grammar: str | None = None,
       stage: str | None = None,
       failures_only: bool = False
   ) -> None:
       """Show recent workshop log events."""
       reader = WorkshopLogReader()
       events = reader.get_recent(limit)

       if grammar:
           events = [e for e in events if e.grammar == grammar]
       if stage:
           events = [e for e in events if e.stage == stage]
       if failures_only:
           events = [e for e in events if e.status == "failure"]

       # Display with rich table
       ...

   @logs_app.command()
   def stats() -> None:
       """Show statistics from workshop logs."""
       reader = WorkshopLogReader()
       stats = reader.calculate_stats()
       # Display stats with rich
       ...
   ```

**Testing Requirements**:
- Test doctor command with various inputs
- Test log viewing commands
- Test filtering options
- Verify rich output formatting

---

#### C2. Document JSONL Log Contract

**Deliverables**:

Create `docs/WORKSHOP_LOGS.md`:

```markdown
# Workshop JSONL Log Format

## Overview

All workshop operations log to `logs/workshop.jsonl` in JSONL format.

## Event Schema

Each line is a JSON object with these fields:

- `timestamp` (string, ISO8601): Event timestamp (UTC)
- `stage` (string): One of: load, generate, fmt, vet, test, doctor
- `status` (string): One of: started, success, failure
- `grammar` (string, optional): Grammar name
- `artifact_paths` (array, optional): Paths to artifacts
- `error` (string, optional): Error message if status=failure
- `duration_ms` (number, optional): Duration in milliseconds
- `metadata` (object, optional): Additional metadata
- `agent_id` (string, optional): Agent identifier
- `session_id` (string, optional): Session identifier
- `user_id` (string, optional): User identifier

## Example Events

### Successful Load
```json
{"timestamp":"2024-01-15T10:30:00Z","stage":"load","status":"success","grammar":"python","duration_ms":150.5}
```

### Failed Generation
```json
{"timestamp":"2024-01-15T10:30:05Z","stage":"generate","status":"failure","grammar":"python","error":"Missing node-types.json","duration_ms":10.2}
```

## Querying with jq

```bash
# Show all failures
jq 'select(.status=="failure")' logs/workshop.jsonl

# Show events for python grammar
jq 'select(.grammar=="python")' logs/workshop.jsonl

# Calculate average duration by stage
jq -s 'group_by(.stage) | map({stage: .[0].stage, avg_duration: (map(.duration_ms) | add / length)})' logs/workshop.jsonl
```
```

**Requirements**:
- Document all fields
- Provide query examples
- Document append-only contract
- Provide parsing examples

**Testing Requirements**:
- Verify jq examples work
- Verify schema documentation is accurate
- Test with real log files

---

## Parallelization Strategy

### Week 1 (Parallel Development)

**Developer A**:
- Track A: Implement WorkshopDoctor (A1)
- Implement diagnostic checks
- Write diagnostic tests

**Developer B**:
- Track B: Implement WorkshopLogger (B1)
- Implement log reader
- Write logging tests

**Sync Point**: Integrate doctor + logging

### Week 2 (Integration)

**Both developers**:
- Track B2: Integrate logging into workflow stages
- Track C1: CLI commands
- Track C2: Documentation
- End-to-end testing

---

## Testing Strategy

### Unit Tests (Per Check)

For each diagnostic check:
- Test with valid input (no issues)
- Test with problematic input (issues found)
- Verify error messages are clear
- Verify suggestions are helpful

### Integration Tests (Complete Doctor Run)

- Run doctor on real grammar
- Verify all checks execute
- Verify report is complete
- Test with various issue combinations

### Logging Tests

- Test JSONL format correctness
- Test concurrent writes
- Test reading and filtering
- Test with malformed entries
- Verify file locking works

### End-to-End Tests

- Run complete workflow
- Verify all stages log events
- Verify timing is captured
- Query logs with jq
- Generate statistics

---

## Verification Checklist

Before marking Phase 4 complete, verify:

### Diagnostic Engine
- [ ] All diagnostic checks implemented
- [ ] Doctor runs without errors
- [ ] All issues have clear messages
- [ ] Suggestions are actionable
- [ ] Report formatting works (terminal, JSON, Markdown)
- [ ] Exit codes correct (0 if healthy, 1 if issues)

### Logging System
- [ ] All workflow stages log events
- [ ] JSONL format is valid
- [ ] Concurrent writes work correctly
- [ ] Log reader can query logs
- [ ] Statistics calculation works
- [ ] jq queries work correctly

### CLI Integration
- [ ] `confidantic workshop doctor` works
- [ ] `confidantic logs show` works
- [ ] `confidantic logs stats` works
- [ ] Rich formatting displays correctly
- [ ] All options work as documented

### Documentation
- [ ] WORKSHOP_LOGS.md is complete
- [ ] Example queries work
- [ ] Schema is documented
- [ ] Usage examples are clear

### Testing
- [ ] All tests pass
- [ ] Code coverage ≥ 90%
- [ ] Integration tests pass
- [ ] Concurrent logging tests pass

---

## Common Pitfalls to Avoid

1. **Non-deterministic log order**: Use timestamps for ordering
2. **Corrupted JSONL**: Always use file locking for concurrent writes
3. **Unclear error messages**: Always include file path + line number
4. **Missing context**: Include enough metadata to debug issues
5. **Blocking on log writes**: Log errors but continue workflow
6. **Large log files**: Consider log rotation (future work)
7. **Timezone confusion**: Always use UTC

---

## Example Usage (After Phase 4)

### Running Diagnostics

```bash
# Run doctor on Python grammar
confidantic workshop doctor \
  --grammar python \
  --node-types build/treesitter/python/node-types.json \
  --queries-dir build/treesitter/python/queries \
  --schemas-dir build/schemas/cue/python

# Export report to JSON
confidantic workshop doctor \
  --grammar python \
  --node-types build/treesitter/python/node-types.json \
  --queries-dir build/treesitter/python/queries \
  --format json \
  --output reports/python-doctor.json
```

### Viewing Logs

```bash
# Show recent events
confidantic logs show --limit 20

# Show failures only
confidantic logs show --failures-only

# Show events for specific grammar
confidantic logs show --grammar python

# Show statistics
confidantic logs stats
```

### Querying Logs with jq

```bash
# All failures
jq 'select(.status=="failure")' logs/workshop.jsonl

# Events for python grammar
jq 'select(.grammar=="python")' logs/workshop.jsonl

# Average duration by stage
jq -s 'group_by(.stage) | map({
  stage: .[0].stage,
  avg_ms: (map(.duration_ms) | add / length)
})' logs/workshop.jsonl

# Failure rate by grammar
jq -s 'group_by(.grammar) | map({
  grammar: .[0].grammar,
  total: length,
  failures: map(select(.status=="failure")) | length
})' logs/workshop.jsonl
```

### Doctor Report Example

```
╭─────────────────────────────────────────────────────────╮
│           Workshop Diagnostics: python                  │
╰─────────────────────────────────────────────────────────╯

✓ Artifacts
  - node-types.json: 487 types
  - queries/highlights.scm: 125 captures
  - queries/tags.scm: 45 captures

⚠ Warnings

  Unmapped Capture
  File: queries/highlights.scm:127
  Message: Capture @functon.definition references unknown node type
  Suggestion: Did you mean @function.definition?

ℹ Info

  Unused Node Types
  Message: 12 node types are never referenced in queries
  Details: comment, block_comment, line_comment, ...

✓ Generated CUE
  - All files valid
  - Deterministic ordering verified
  - No performance issues

╭─────────────────────────────────────────────────────────╮
│                      Summary                            │
│  Checks run: 8                                          │
│  Errors: 0                                              │
│  Warnings: 1                                            │
│  Info: 1                                                │
│                                                         │
│  Status: HEALTHY ✓                                      │
╰─────────────────────────────────────────────────────────╯
```

---

## Exit Criteria

Phase 4 is complete when:

1. WorkshopDoctor runs all diagnostic checks
2. Diagnostic reports are clear and actionable
3. All workflow stages log to workshop.jsonl
4. JSONL logs are queryable with jq
5. CLI commands work correctly
6. Documentation is complete
7. All tests pass (coverage ≥ 90%)
8. All items in verification checklist checked off

**Next Phase**: Phase 5 - CLI plumbing and migration compatibility

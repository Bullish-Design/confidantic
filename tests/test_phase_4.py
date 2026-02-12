"""
Phase 4 Validation Test Suite

This test file provides a quick check that Phase 4 (Doctoring, Diagnostics, and Provenance)
is complete and working correctly.

Run with: pytest tests/test_phase_4.py -v
"""

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Import previous phase components
try:
    from confidantic.workshop.generator import CueGenerator
    from confidantic.workshop.loaders import load_workshop_input

    PHASE_3_AVAILABLE = True
except ImportError:
    PHASE_3_AVAILABLE = False

# Try to import Phase 4 deliverables
try:
    from confidantic.workshop.doctor import DiagnosticIssue, DiagnosticReport, WorkshopDoctor

    DOCTOR_AVAILABLE = True
except ImportError:
    DOCTOR_AVAILABLE = False

try:
    from confidantic.workshop.logging import WorkshopEvent, WorkshopLogger, WorkshopLogReader

    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False


class TestPhase4Prerequisites:
    """Verify Phase 4 deliverables exist."""

    def test_phase_3_complete(self):
        """Verify Phase 3 is complete (required for Phase 4)."""
        assert PHASE_3_AVAILABLE, (
            "Phase 3 must be complete before Phase 4! "
            "Run: pytest tests/test_phase_3.py"
        )

    def test_doctor_module_exists(self):
        """Verify src/confidantic/workshop/doctor.py exists."""
        doctor_file = Path("src/confidantic/workshop/doctor.py")
        assert doctor_file.exists(), (
            "doctor.py not found! Create src/confidantic/workshop/doctor.py"
        )

    def test_logging_module_exists(self):
        """Verify src/confidantic/workshop/logging.py exists."""
        logging_file = Path("src/confidantic/workshop/logging.py")
        assert logging_file.exists(), (
            "logging.py not found! Create src/confidantic/workshop/logging.py"
        )


@pytest.mark.skipif(not DOCTOR_AVAILABLE, reason="Doctor module not yet implemented")
class TestPhase4Doctor:
    """Verify WorkshopDoctor is implemented correctly."""

    def test_workshop_doctor_class_exists(self):
        """Verify WorkshopDoctor class is defined."""
        assert hasattr(WorkshopDoctor, "__init__"), "WorkshopDoctor must be a class"

    def test_workshop_doctor_has_run_diagnostics(self):
        """Verify WorkshopDoctor has run_diagnostics method."""
        assert hasattr(WorkshopDoctor, "run_diagnostics"), (
            "WorkshopDoctor must have run_diagnostics() method"
        )

    def test_diagnostic_issue_model_exists(self):
        """Verify DiagnosticIssue model is defined."""
        assert hasattr(DiagnosticIssue, "model_fields"), (
            "DiagnosticIssue must be a Pydantic model"
        )

    def test_diagnostic_report_model_exists(self):
        """Verify DiagnosticReport model is defined."""
        assert hasattr(DiagnosticReport, "model_fields"), (
            "DiagnosticReport must be a Pydantic model"
        )

    def test_diagnostic_report_has_is_healthy(self):
        """Verify DiagnosticReport has is_healthy method."""
        assert hasattr(DiagnosticReport, "is_healthy"), (
            "DiagnosticReport must have is_healthy() method"
        )


@pytest.mark.skipif(not LOGGING_AVAILABLE, reason="Logging module not yet implemented")
class TestPhase4Logging:
    """Verify WorkshopLogger is implemented correctly."""

    def test_workshop_logger_class_exists(self):
        """Verify WorkshopLogger class is defined."""
        assert hasattr(WorkshopLogger, "__init__"), "WorkshopLogger must be a class"

    def test_workshop_logger_has_log_event(self):
        """Verify WorkshopLogger has log_event method."""
        assert hasattr(WorkshopLogger, "log_event"), (
            "WorkshopLogger must have log_event() method"
        )

    def test_workshop_log_reader_class_exists(self):
        """Verify WorkshopLogReader class is defined."""
        assert hasattr(WorkshopLogReader, "__init__"), "WorkshopLogReader must be a class"

    def test_workshop_log_reader_has_read_all(self):
        """Verify WorkshopLogReader has read_all method."""
        assert hasattr(WorkshopLogReader, "read_all"), (
            "WorkshopLogReader must have read_all() method"
        )

    def test_workshop_event_has_to_jsonl(self):
        """Verify WorkshopEvent has to_jsonl method."""
        assert hasattr(WorkshopEvent, "to_jsonl"), (
            "WorkshopEvent must have to_jsonl() method"
        )

    def test_workshop_event_has_from_jsonl(self):
        """Verify WorkshopEvent has from_jsonl class method."""
        assert hasattr(WorkshopEvent, "from_jsonl"), (
            "WorkshopEvent must have from_jsonl() class method"
        )


@pytest.mark.skipif(not LOGGING_AVAILABLE, reason="Logging module required")
class TestPhase4LoggingIntegration:
    """Integration tests for logging functionality."""

    def test_workshop_event_jsonl_roundtrip(self):
        """Test WorkshopEvent serialization and deserialization."""
        event = WorkshopEvent(
            timestamp=datetime.now(timezone.utc),
            stage="load",
            status="success",
            grammar="test",
            duration_ms=150.5,
        )

        # Serialize to JSONL
        jsonl_str = event.to_jsonl()

        # Verify it's valid JSON
        parsed = json.loads(jsonl_str)
        assert parsed["stage"] == "load"
        assert parsed["status"] == "success"
        assert parsed["grammar"] == "test"

        # Deserialize back
        event2 = WorkshopEvent.from_jsonl(jsonl_str)
        assert event2.stage == event.stage
        assert event2.status == event.status
        assert event2.grammar == event.grammar

    def test_workshop_logger_logs_events(self, tmp_path: Path):
        """Test that WorkshopLogger can log events."""
        log_file = tmp_path / "test-workshop.jsonl"

        logger = WorkshopLogger(log_path=log_file)

        # Log some events
        logger.log_event(
            stage="load",
            status="started",
            grammar="test"
        )

        time.sleep(0.01)  # Small delay

        logger.log_event(
            stage="load",
            status="success",
            grammar="test",
            duration_ms=10.5
        )

        # Verify log file was created
        assert log_file.exists(), "Log file should be created"

        # Verify contents
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2, "Should have 2 log entries"

        # Verify entries are valid JSON
        for line in lines:
            event_data = json.loads(line)
            assert "timestamp" in event_data
            assert "stage" in event_data
            assert "status" in event_data

    def test_workshop_log_reader_reads_events(self, tmp_path: Path):
        """Test that WorkshopLogReader can read logged events."""
        log_file = tmp_path / "test-workshop.jsonl"

        # Write some events
        logger = WorkshopLogger(log_path=log_file)
        logger.log_event(stage="load", status="success", grammar="python")
        logger.log_event(stage="generate", status="success", grammar="python")
        logger.log_event(stage="vet", status="failure", grammar="rust", error="Invalid CUE")

        # Read them back
        reader = WorkshopLogReader(log_path=log_file)
        events = reader.read_all()

        assert len(events) == 3, "Should read all 3 events"
        assert all(isinstance(e, WorkshopEvent) for e in events)
        assert events[0].stage == "load"
        assert events[1].stage == "generate"
        assert events[2].stage == "vet"

    def test_workshop_log_reader_filters_by_grammar(self, tmp_path: Path):
        """Test filtering events by grammar."""
        log_file = tmp_path / "test-workshop.jsonl"

        logger = WorkshopLogger(log_path=log_file)
        logger.log_event(stage="load", status="success", grammar="python")
        logger.log_event(stage="load", status="success", grammar="rust")
        logger.log_event(stage="generate", status="success", grammar="python")

        reader = WorkshopLogReader(log_path=log_file)
        python_events = reader.filter_by_grammar("python")

        assert len(python_events) == 2, "Should find 2 python events"
        assert all(e.grammar == "python" for e in python_events)

    def test_workshop_log_reader_gets_failures(self, tmp_path: Path):
        """Test getting failure events."""
        log_file = tmp_path / "test-workshop.jsonl"

        logger = WorkshopLogger(log_path=log_file)
        logger.log_event(stage="load", status="success", grammar="python")
        logger.log_event(stage="generate", status="failure", grammar="python", error="Missing file")
        logger.log_event(stage="vet", status="failure", grammar="rust", error="Invalid CUE")

        reader = WorkshopLogReader(log_path=log_file)
        failures = reader.get_failures()

        assert len(failures) == 2, "Should find 2 failures"
        assert all(e.status == "failure" for e in failures)


@pytest.mark.skipif(
    not DOCTOR_AVAILABLE,
    reason="Doctor module required"
)
class TestPhase4DoctorIntegration:
    """Integration tests for doctor functionality."""

    @pytest.fixture
    def sample_artifacts(self, tmp_path: Path):
        """Create sample Tree-sitter artifacts."""
        import json

        node_types_data = [
            {"type": "module", "named": True},
            {"type": "identifier", "named": True},
        ]
        node_types_file = tmp_path / "node-types.json"
        node_types_file.write_text(json.dumps(node_types_data))

        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        (queries_dir / "highlights.scm").write_text("(identifier) @variable")

        return {
            "grammar": "test",
            "node_types": node_types_file,
            "queries_dir": queries_dir,
        }

    def test_doctor_runs_on_valid_artifacts(self, sample_artifacts):
        """Test doctor runs successfully on valid artifacts."""
        doctor = WorkshopDoctor(
            grammar=sample_artifacts["grammar"],
            node_types_path=sample_artifacts["node_types"],
            queries_dir=sample_artifacts["queries_dir"]
        )

        report = doctor.run_diagnostics()

        assert isinstance(report, DiagnosticReport)
        assert report.grammar == "test"
        assert report.checks_run > 0

    def test_doctor_detects_missing_file(self, tmp_path: Path):
        """Test doctor detects missing node-types.json."""
        doctor = WorkshopDoctor(
            grammar="test",
            node_types_path=tmp_path / "nonexistent.json",
            queries_dir=tmp_path / "queries"
        )

        report = doctor.run_diagnostics()

        # Should report an error about missing file
        assert len(report.errors) > 0 or not report.is_healthy()

    def test_diagnostic_report_is_healthy(self, sample_artifacts):
        """Test DiagnosticReport.is_healthy() method."""
        doctor = WorkshopDoctor(
            grammar=sample_artifacts["grammar"],
            node_types_path=sample_artifacts["node_types"],
            queries_dir=sample_artifacts["queries_dir"]
        )

        report = doctor.run_diagnostics()

        # Should be healthy or unhealthy based on errors
        health_status = report.is_healthy()
        assert isinstance(health_status, bool)

        # If healthy, should have no errors
        if health_status:
            assert len(report.errors) == 0


@pytest.mark.skipif(
    not LOGGING_AVAILABLE,
    reason="Logging module required"
)
class TestPhase4ConcurrentLogging:
    """Test concurrent logging safety."""

    def test_concurrent_logging(self, tmp_path: Path):
        """Test that concurrent logging doesn't corrupt JSONL."""
        import threading

        log_file = tmp_path / "concurrent.jsonl"
        logger = WorkshopLogger(log_path=log_file)

        def log_events(thread_id: int, count: int):
            for i in range(count):
                logger.log_event(
                    stage="test",
                    status="success",
                    grammar=f"thread{thread_id}",
                    metadata={"thread": thread_id, "iteration": i}
                )

        # Run multiple threads logging concurrently
        threads = []
        for i in range(5):
            t = threading.Thread(target=log_events, args=(i, 10))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify all events were logged
        reader = WorkshopLogReader(log_path=log_file)
        events = reader.read_all()

        # Should have 5 threads * 10 events = 50 total
        assert len(events) == 50, f"Expected 50 events, got {len(events)}"

        # Verify all lines are valid JSON
        lines = log_file.read_text().strip().split("\n")
        for line in lines:
            json.loads(line)  # Should not raise


# Summary test
def test_phase_4_summary():
    """Print a summary of Phase 4 completion status."""
    summary = {
        "Phase 3 Complete": PHASE_3_AVAILABLE,
        "Doctor Module Available": DOCTOR_AVAILABLE,
        "Logging Module Available": LOGGING_AVAILABLE,
        "Phase 4 Complete": PHASE_3_AVAILABLE and DOCTOR_AVAILABLE and LOGGING_AVAILABLE,
    }

    # Check for logs directory
    logs_dir = Path("logs")
    summary["Logs Directory Exists"] = logs_dir.exists()

    print("\n" + "=" * 60)
    print("PHASE 4 VALIDATION SUMMARY")
    print("=" * 60)
    for key, value in summary.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    print("=" * 60)

    if not summary["Phase 4 Complete"]:
        print("\nPhase 4 is NOT complete. Missing components:")
        if not PHASE_3_AVAILABLE:
            print("  - Phase 3 must be completed first!")
        if not DOCTOR_AVAILABLE:
            print("  - src/confidantic/workshop/doctor.py")
        if not LOGGING_AVAILABLE:
            print("  - src/confidantic/workshop/logging.py")
        print("\nRefer to ROADMAP-PHASE_4.md for implementation guidance.")
    else:
        print("\n✓ Phase 4 is COMPLETE! All required components are implemented.")
        print("  Diagnostics and provenance logging are ready.")
        print("  Ready to proceed to Phase 5: CLI plumbing and migration compatibility")

    if not logs_dir.exists():
        print("\n⚠ Note: logs/ directory doesn't exist yet (will be created on first log)")

    print("=" * 60 + "\n")

    assert summary["Phase 4 Complete"], "Phase 4 is not yet complete"

"""
Phase 1 Validation Test Suite

This test file provides a quick check that Phase 1 (Workshop Input Model and Ingestion)
is complete and working correctly.

Run with: pytest tests/test_phase_1.py -v
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

# Try to import Phase 1 deliverables
try:
    from confidantic.workshop.models import (
        NodeType,
        NodeTypes,
        QueryCapture,
        QueryFile,
        WorkshopEvent,
        WorkshopInput,
    )

    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

try:
    from confidantic.workshop.loaders import (
        discover_query_files,
        load_node_types,
        load_query_file,
        load_workshop_event,
        load_workshop_input,
        log_workshop_event,
    )

    LOADERS_AVAILABLE = True
except ImportError:
    LOADERS_AVAILABLE = False


class TestPhase1Prerequisites:
    """Verify Phase 1 deliverables exist."""

    def test_models_module_exists(self):
        """Verify src/confidantic/workshop/models.py exists."""
        models_file = Path("src/confidantic/workshop/models.py")
        assert models_file.exists(), "models.py not found! Create src/confidantic/workshop/models.py"

    def test_loaders_module_exists(self):
        """Verify src/confidantic/workshop/loaders.py exists."""
        loaders_file = Path("src/confidantic/workshop/loaders.py")
        assert loaders_file.exists(), "loaders.py not found! Create src/confidantic/workshop/loaders.py"

    def test_workshop_package_exists(self):
        """Verify src/confidantic/workshop/ package exists."""
        workshop_pkg = Path("src/confidantic/workshop/__init__.py")
        assert workshop_pkg.exists(), "__init__.py not found! Create src/confidantic/workshop/__init__.py"


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models module not yet implemented")
class TestPhase1Models:
    """Verify all required models are implemented."""

    def test_node_type_model_exists(self):
        """Verify NodeType model is defined."""
        assert hasattr(NodeType, "model_fields"), "NodeType must be a Pydantic model"

    def test_node_types_model_exists(self):
        """Verify NodeTypes model is defined."""
        assert hasattr(NodeTypes, "model_fields"), "NodeTypes must be a Pydantic model"

    def test_query_capture_model_exists(self):
        """Verify QueryCapture model is defined."""
        assert hasattr(QueryCapture, "model_fields"), "QueryCapture must be a Pydantic model"

    def test_query_file_model_exists(self):
        """Verify QueryFile model is defined."""
        assert hasattr(QueryFile, "model_fields"), "QueryFile must be a Pydantic model"

    def test_workshop_input_model_exists(self):
        """Verify WorkshopInput model is defined."""
        assert hasattr(WorkshopInput, "model_fields"), "WorkshopInput must be a Pydantic model"

    def test_workshop_event_model_exists(self):
        """Verify WorkshopEvent model is defined."""
        assert hasattr(WorkshopEvent, "model_fields"), "WorkshopEvent must be a Pydantic model"

    def test_workshop_event_to_jsonl(self):
        """Verify WorkshopEvent can serialize to JSONL."""
        event = WorkshopEvent(
            timestamp=datetime.now(timezone.utc),
            stage="load",
            status="success",
            grammar="test",
        )
        jsonl_str = event.to_jsonl()
        assert isinstance(jsonl_str, str), "to_jsonl() must return string"
        # Verify it's valid JSON
        parsed = json.loads(jsonl_str)
        assert parsed["stage"] == "load"
        assert parsed["status"] == "success"

    def test_node_types_deterministic_ordering(self):
        """Verify NodeTypes sorts nodes deterministically."""
        node_data = [
            {"type": "zebra", "named": True},
            {"type": "apple", "named": True},
            {"type": "middle", "named": False},
        ]

        # Create model multiple times
        results = []
        for _ in range(3):
            nt = NodeTypes(nodes=node_data)
            results.append([n.type for n in nt.nodes])

        # All results should be identical and sorted
        assert all(r == results[0] for r in results), "NodeTypes ordering is non-deterministic!"
        assert results[0] == sorted(results[0]), "NodeTypes nodes must be sorted by type name"


@pytest.mark.skipif(not LOADERS_AVAILABLE, reason="Loaders module not yet implemented")
class TestPhase1Loaders:
    """Verify all required loader functions are implemented."""

    def test_load_node_types_exists(self):
        """Verify load_node_types function exists."""
        assert callable(load_node_types), "load_node_types must be a callable function"

    def test_load_query_file_exists(self):
        """Verify load_query_file function exists."""
        assert callable(load_query_file), "load_query_file must be a callable function"

    def test_discover_query_files_exists(self):
        """Verify discover_query_files function exists."""
        assert callable(discover_query_files), "discover_query_files must be a callable function"

    def test_load_workshop_input_exists(self):
        """Verify load_workshop_input function exists."""
        assert callable(load_workshop_input), "load_workshop_input must be a callable function"

    def test_log_workshop_event_exists(self):
        """Verify log_workshop_event function exists."""
        assert callable(log_workshop_event), "log_workshop_event must be a callable function"

    def test_load_workshop_events_exists(self):
        """Verify load_workshop_events function exists."""
        assert callable(load_workshop_event), "load_workshop_events must be a callable function"


@pytest.mark.skipif(
    not (MODELS_AVAILABLE and LOADERS_AVAILABLE),
    reason="Models or loaders not yet implemented"
)
class TestPhase1Integration:
    """Integration tests for Phase 1 functionality."""

    @pytest.fixture
    def temp_node_types_file(self, tmp_path: Path) -> Path:
        """Create a temporary node-types.json file."""
        node_types_data = [
            {
                "type": "module",
                "named": True,
                "fields": {},
            },
            {
                "type": "identifier",
                "named": True,
                "fields": {},
            },
        ]

        node_types_file = tmp_path / "node-types.json"
        node_types_file.write_text(json.dumps(node_types_data, indent=2))
        return node_types_file

    @pytest.fixture
    def temp_query_file(self, tmp_path: Path) -> Path:
        """Create a temporary query .scm file."""
        query_content = """
; Function definitions
(function_definition
  name: (identifier) @function.definition)

; Classes
(class_definition
  name: (identifier) @class.definition)
"""
        query_file = tmp_path / "highlights.scm"
        query_file.write_text(query_content)
        return query_file

    def test_load_node_types_integration(self, temp_node_types_file: Path):
        """Test loading a real node-types.json file."""
        node_types = load_node_types(temp_node_types_file)

        assert isinstance(node_types, NodeTypes)
        assert len(node_types.nodes) == 2
        # Verify deterministic ordering (alphabetical)
        assert node_types.nodes[0].type == "identifier"
        assert node_types.nodes[1].type == "module"

    def test_load_query_file_integration(self, temp_query_file: Path):
        """Test loading a real .scm query file."""
        query_file_obj = load_query_file(temp_query_file, query_type="highlights")

        assert isinstance(query_file_obj, QueryFile)
        assert query_file_obj.query_type == "highlights"
        assert len(query_file_obj.captures) > 0

        # Verify captures are extracted
        capture_names = [c.name for c in query_file_obj.captures]
        assert "@function.definition" in capture_names or "@class.definition" in capture_names

    def test_discover_query_files_determinism(self, tmp_path: Path):
        """Test that query file discovery is deterministic."""
        # Create multiple .scm files
        (tmp_path / "zebra.scm").write_text("; test")
        (tmp_path / "apple.scm").write_text("; test")
        (tmp_path / "middle.scm").write_text("; test")

        # Run discovery multiple times
        results = []
        for _ in range(5):
            discovered = discover_query_files(tmp_path)
            results.append([f.name for f in discovered])

        # All results should be identical and sorted
        assert all(r == results[0] for r in results), "File discovery is non-deterministic!"
        assert results[0] == sorted(results[0]), "Files must be sorted alphabetically"

    def test_workshop_event_logging_roundtrip(self, tmp_path: Path):
        """Test logging and loading workshop events."""
        log_file = tmp_path / "test-workshop.jsonl"

        # Create and log events
        events_to_log = [
            WorkshopEvent(
                timestamp=datetime.now(timezone.utc),
                stage="load",
                status="started",
                grammar="test",
            ),
            WorkshopEvent(
                timestamp=datetime.now(timezone.utc),
                stage="load",
                status="success",
                grammar="test",
            ),
        ]

        for event in events_to_log:
            log_workshop_event(event, log_file)

        # Load events back
        loaded_events = load_workshop_events(log_file)

        assert len(loaded_events) == 2
        assert loaded_events[0].stage == "load"
        assert loaded_events[0].status == "started"
        assert loaded_events[1].status == "success"


@pytest.mark.skipif(
    not (MODELS_AVAILABLE and LOADERS_AVAILABLE),
    reason="Models or loaders not yet implemented"
)
class TestPhase1Determinism:
    """Golden tests for deterministic behavior."""

    @pytest.fixture
    def sample_grammar_artifacts(self, tmp_path: Path) -> tuple[str, Path, Path]:
        """Create sample Tree-sitter grammar artifacts."""
        grammar_name = "sample"

        # Create node-types.json
        node_types_data = [
            {"type": "statement", "named": True},
            {"type": "expression", "named": True},
            {"type": "identifier", "named": True},
        ]
        node_types_file = tmp_path / "node-types.json"
        node_types_file.write_text(json.dumps(node_types_data))

        # Create queries directory
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()

        # Create query files
        (queries_dir / "highlights.scm").write_text(
            "(identifier) @variable\n(statement) @keyword"
        )
        (queries_dir / "tags.scm").write_text(
            "(identifier) @name\n(expression) @reference"
        )

        return grammar_name, node_types_file, queries_dir

    def test_fingerprint_stability(self, sample_grammar_artifacts):
        """Verify that loading the same input produces the same fingerprint."""
        grammar_name, node_types_file, queries_dir = sample_grammar_artifacts

        fingerprints = []
        for _ in range(10):
            workshop_input = load_workshop_input(
                grammar_name=grammar_name,
                node_types_path=node_types_file,
                queries_dir=queries_dir,
            )
            fingerprints.append(workshop_input.fingerprint())

        # All fingerprints must be identical
        unique_fingerprints = set(fingerprints)
        assert len(unique_fingerprints) == 1, (
            f"Non-deterministic fingerprints detected! "
            f"Got {len(unique_fingerprints)} unique values: {unique_fingerprints}"
        )

    def test_workshop_input_deterministic_structure(self, sample_grammar_artifacts):
        """Verify that WorkshopInput structure is deterministic."""
        grammar_name, node_types_file, queries_dir = sample_grammar_artifacts

        results = []
        for _ in range(5):
            workshop_input = load_workshop_input(
                grammar_name=grammar_name,
                node_types_path=node_types_file,
                queries_dir=queries_dir,
            )

            # Extract structure
            structure = {
                "node_count": len(workshop_input.node_types.nodes),
                "node_order": [n.type for n in workshop_input.node_types.nodes],
                "query_count": len(workshop_input.query_files),
                "query_order": [qf.file_path.name for qf in workshop_input.query_files],
            }
            results.append(structure)

        # All results should be identical
        for i in range(1, len(results)):
            assert results[i] == results[0], (
                f"Run {i} produced different structure than run 0:\n"
                f"Run 0: {results[0]}\n"
                f"Run {i}: {results[i]}"
            )


# Summary test to run at the end
def test_phase_1_summary():
    """Print a summary of Phase 1 completion status."""
    summary = {
        "Models Available": MODELS_AVAILABLE,
        "Loaders Available": LOADERS_AVAILABLE,
        "Phase 1 Complete": MODELS_AVAILABLE and LOADERS_AVAILABLE,
    }

    print("\n" + "=" * 60)
    print("PHASE 1 VALIDATION SUMMARY")
    print("=" * 60)
    for key, value in summary.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    print("=" * 60)

    if not summary["Phase 1 Complete"]:
        print("\nPhase 1 is NOT complete. Missing components:")
        if not MODELS_AVAILABLE:
            print("  - src/confidantic/workshop/models.py")
        if not LOADERS_AVAILABLE:
            print("  - src/confidantic/workshop/loaders.py")
        print("\nRefer to ROADMAP-PHASE_1.md for implementation guidance.")
    else:
        print("\n✓ Phase 1 is COMPLETE! All required components are implemented.")
        print("  Ready to proceed to Phase 2: Deterministic CUE generation engine")

    print("=" * 60 + "\n")

    assert summary["Phase 1 Complete"], "Phase 1 is not yet complete"

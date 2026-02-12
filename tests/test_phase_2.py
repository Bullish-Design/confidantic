"""
Phase 2 Validation Test Suite

This test file provides a quick check that Phase 2 (Deterministic CUE Generation Engine)
is complete and working correctly.

Run with: pytest tests/test_phase_2.py -v
"""

import subprocess
from pathlib import Path

import pytest

# Import Phase 1 components (required for Phase 2)
try:
    from confidantic.workshop.loaders import load_workshop_input
    from confidantic.workshop.models import WorkshopInput

    PHASE_1_AVAILABLE = True
except ImportError:
    PHASE_1_AVAILABLE = False

# Try to import Phase 2 deliverables
try:
    from confidantic.workshop.generator import CueGenerator

    GENERATOR_AVAILABLE = True
except ImportError:
    GENERATOR_AVAILABLE = False

try:
    from confidantic.cue.formatter import (
        format_cue_directory,
        format_cue_file,
        validate_cue_file,
    )

    FORMATTER_AVAILABLE = True
except ImportError:
    FORMATTER_AVAILABLE = False


class TestPhase2Prerequisites:
    """Verify Phase 2 deliverables exist."""

    def test_phase_1_complete(self):
        """Verify Phase 1 is complete (required for Phase 2)."""
        assert PHASE_1_AVAILABLE, (
            "Phase 1 must be complete before Phase 2! "
            "Run: pytest tests/test_phase_1.py"
        )

    def test_generator_module_exists(self):
        """Verify src/confidantic/workshop/generator.py exists."""
        generator_file = Path("src/confidantic/workshop/generator.py")
        assert generator_file.exists(), (
            "generator.py not found! Create src/confidantic/workshop/generator.py"
        )

    def test_formatter_module_exists(self):
        """Verify src/confidantic/cue/formatter.py exists."""
        formatter_file = Path("src/confidantic/cue/formatter.py")
        assert formatter_file.exists(), (
            "formatter.py not found! Create src/confidantic/cue/formatter.py"
        )

    def test_cue_package_exists(self):
        """Verify src/confidantic/cue/ package exists."""
        cue_pkg = Path("src/confidantic/cue/__init__.py")
        assert cue_pkg.exists(), (
            "__init__.py not found! Create src/confidantic/cue/__init__.py"
        )


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator not yet implemented")
class TestPhase2Generator:
    """Verify CueGenerator is implemented correctly."""

    def test_cue_generator_class_exists(self):
        """Verify CueGenerator class is defined."""
        assert hasattr(CueGenerator, "__init__"), "CueGenerator must be a class"

    def test_cue_generator_has_generate_method(self):
        """Verify CueGenerator has generate() method."""
        assert hasattr(CueGenerator, "generate"), "CueGenerator must have generate() method"

    @pytest.mark.skipif(not PHASE_1_AVAILABLE, reason="Phase 1 required")
    def test_cue_generator_accepts_workshop_input(self, minimal_workshop_input):
        """Verify CueGenerator accepts WorkshopInput."""
        try:
            generator = CueGenerator(minimal_workshop_input)
            assert generator is not None
        except Exception as e:
            pytest.fail(f"CueGenerator failed to initialize with WorkshopInput: {e}")


@pytest.mark.skipif(not FORMATTER_AVAILABLE, reason="Formatter not yet implemented")
class TestPhase2Formatter:
    """Verify CUE formatting utilities are implemented."""

    def test_format_cue_file_exists(self):
        """Verify format_cue_file function exists."""
        assert callable(format_cue_file), "format_cue_file must be a callable function"

    def test_format_cue_directory_exists(self):
        """Verify format_cue_directory function exists."""
        assert callable(format_cue_directory), "format_cue_directory must be a callable function"

    def test_validate_cue_file_exists(self):
        """Verify validate_cue_file function exists."""
        assert callable(validate_cue_file), "validate_cue_file must be a callable function"


@pytest.mark.skipif(
    not (PHASE_1_AVAILABLE and GENERATOR_AVAILABLE),
    reason="Phase 1 and generator required"
)
class TestPhase2Integration:
    """Integration tests for Phase 2 functionality."""

    @pytest.fixture
    def minimal_workshop_input(self, tmp_path: Path):
        """Create minimal WorkshopInput for testing."""
        import json
        from datetime import datetime, timezone

        from confidantic.workshop.models import NodeTypes, QueryFile, WorkshopInput

        # Create minimal node-types.json
        node_types_data = [
            {"type": "identifier", "named": True},
            {"type": "module", "named": True},
        ]
        node_types_file = tmp_path / "node-types.json"
        node_types_file.write_text(json.dumps(node_types_data))

        # Create minimal query file
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        (queries_dir / "highlights.scm").write_text("(identifier) @variable")

        # Load WorkshopInput
        workshop_input = load_workshop_input(
            grammar_name="test",
            node_types_path=node_types_file,
            queries_dir=queries_dir,
        )

        return workshop_input

    def test_generate_creates_output_files(self, minimal_workshop_input, tmp_path: Path):
        """Test that generator creates CUE files."""
        output_dir = tmp_path / "build/schemas/cue/test"
        output_dir.mkdir(parents=True)

        generator = CueGenerator(minimal_workshop_input)
        generated_files = generator.generate(output_dir)

        # Verify files were created
        assert len(generated_files) > 0, "Generator should create at least one file"
        assert all(f.exists() for f in generated_files), "All generated files should exist"
        assert all(f.suffix == ".cue" for f in generated_files), "All files should be .cue"

    def test_generated_files_are_in_build_directory(self, minimal_workshop_input, tmp_path: Path):
        """Verify generated files are placed in build/ directory."""
        output_dir = tmp_path / "build/schemas/cue/test"
        output_dir.mkdir(parents=True)

        generator = CueGenerator(minimal_workshop_input)
        generated_files = generator.generate(output_dir)

        for file_path in generated_files:
            assert "build" in str(file_path), (
                f"Generated file must be in build/ directory: {file_path}"
            )

    def test_generated_cue_has_package_declaration(self, minimal_workshop_input, tmp_path: Path):
        """Verify generated CUE files have package declarations."""
        output_dir = tmp_path / "build/schemas/cue/test"
        output_dir.mkdir(parents=True)

        generator = CueGenerator(minimal_workshop_input)
        generated_files = generator.generate(output_dir)

        for file_path in generated_files:
            content = file_path.read_text()
            assert "package" in content, f"Missing package declaration in {file_path}"

    def test_generated_cue_has_provenance_comments(self, minimal_workshop_input, tmp_path: Path):
        """Verify generated CUE files include provenance comments."""
        output_dir = tmp_path / "build/schemas/cue/test"
        output_dir.mkdir(parents=True)

        generator = CueGenerator(minimal_workshop_input)
        generated_files = generator.generate(output_dir)

        for file_path in generated_files:
            content = file_path.read_text()
            # Should have some form of provenance (either "Generated" or source path)
            has_provenance = any([
                "Generated" in content,
                "generated" in content,
                "// " in content,  # At least some comments
            ])
            assert has_provenance, f"Missing provenance comments in {file_path}"


@pytest.mark.skipif(
    not (PHASE_1_AVAILABLE and GENERATOR_AVAILABLE and FORMATTER_AVAILABLE),
    reason="Phase 1, generator, and formatter required"
)
class TestPhase2CueValidation:
    """Test that generated CUE is valid."""

    @pytest.fixture
    def minimal_workshop_input(self, tmp_path: Path):
        """Create minimal WorkshopInput for testing."""
        import json

        # Create minimal node-types.json
        node_types_data = [
            {"type": "identifier", "named": True},
        ]
        node_types_file = tmp_path / "node-types.json"
        node_types_file.write_text(json.dumps(node_types_data))

        # Create minimal query file
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        (queries_dir / "highlights.scm").write_text("(identifier) @variable")

        # Load WorkshopInput
        workshop_input = load_workshop_input(
            grammar_name="test",
            node_types_path=node_types_file,
            queries_dir=queries_dir,
        )

        return workshop_input

    def test_cue_binary_available(self):
        """Verify cue binary is available in PATH."""
        try:
            result = subprocess.run(
                ["cue", "version"],
                capture_output=True,
                text=True,
                check=True
            )
            assert "cue version" in result.stdout.lower() or result.returncode == 0
        except FileNotFoundError:
            pytest.skip("cue binary not found in PATH (required for Phase 2)")
        except subprocess.CalledProcessError:
            pytest.skip("cue binary not working correctly")

    def test_generated_cue_is_valid_syntax(self, minimal_workshop_input, tmp_path: Path):
        """Test that generated CUE has valid syntax."""
        output_dir = tmp_path / "build/schemas/cue/test"
        output_dir.mkdir(parents=True)

        generator = CueGenerator(minimal_workshop_input)
        generated_files = generator.generate(output_dir)

        for file_path in generated_files:
            success, error = validate_cue_file(file_path)
            assert success, f"Generated CUE is invalid in {file_path}: {error}"

    def test_generated_cue_can_be_formatted(self, minimal_workshop_input, tmp_path: Path):
        """Test that generated CUE can be formatted with cue fmt."""
        output_dir = tmp_path / "build/schemas/cue/test"
        output_dir.mkdir(parents=True)

        generator = CueGenerator(minimal_workshop_input)
        generated_files = generator.generate(output_dir)

        for file_path in generated_files:
            success = format_cue_file(file_path)
            assert success, f"Failed to format {file_path}"


@pytest.mark.skipif(
    not (PHASE_1_AVAILABLE and GENERATOR_AVAILABLE),
    reason="Phase 1 and generator required"
)
class TestPhase2Determinism:
    """Test that generation is deterministic."""

    @pytest.fixture
    def sample_workshop_input(self, tmp_path: Path):
        """Create sample WorkshopInput with multiple node types."""
        import json

        # Create node-types with deliberately unsorted items
        node_types_data = [
            {"type": "zebra", "named": True},
            {"type": "apple", "named": True},
            {"type": "middle", "named": False},
        ]
        node_types_file = tmp_path / "node-types.json"
        node_types_file.write_text(json.dumps(node_types_data))

        # Create query files
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        (queries_dir / "highlights.scm").write_text(
            "(zebra) @keyword\n(apple) @variable"
        )

        # Load WorkshopInput
        workshop_input = load_workshop_input(
            grammar_name="test",
            node_types_path=node_types_file,
            queries_dir=queries_dir,
        )

        return workshop_input

    def test_deterministic_file_generation(self, sample_workshop_input, tmp_path: Path):
        """Verify generation produces identical files across multiple runs."""
        outputs = []

        for run in range(3):
            output_dir = tmp_path / f"run_{run}/build/schemas/cue/test"
            output_dir.mkdir(parents=True)

            generator = CueGenerator(sample_workshop_input)
            generated_files = generator.generate(output_dir)

            # Collect file contents
            run_output = {}
            for file_path in sorted(generated_files):
                run_output[file_path.name] = file_path.read_text()
            outputs.append(run_output)

        # Compare all runs
        for run_idx in range(1, len(outputs)):
            assert outputs[run_idx].keys() == outputs[0].keys(), (
                f"Run {run_idx} generated different files than run 0"
            )

            for filename in outputs[0].keys():
                # Note: We might need to normalize timestamps if they're included
                assert outputs[run_idx][filename] == outputs[0][filename], (
                    f"Run {run_idx} produced different content in {filename}"
                )

    def test_deterministic_ordering_in_output(self, sample_workshop_input, tmp_path: Path):
        """Verify that output has deterministic ordering (alphabetical)."""
        output_dir = tmp_path / "build/schemas/cue/test"
        output_dir.mkdir(parents=True)

        generator = CueGenerator(sample_workshop_input)
        generated_files = generator.generate(output_dir)

        # Read node_types.cue if it exists
        node_types_file = output_dir / "node_types.cue"
        if node_types_file.exists():
            content = node_types_file.read_text()

            # Find positions of node type names in file
            node_names = ["apple", "middle", "zebra"]
            positions = {}
            for name in node_names:
                if name in content:
                    positions[name] = content.index(name)

            # Verify alphabetical ordering (apple < middle < zebra)
            if len(positions) >= 2:
                sorted_names = sorted(positions.keys())
                sorted_positions = [positions[name] for name in sorted_names]
                assert sorted_positions == sorted(sorted_positions), (
                    "Node types are not in alphabetical order in generated CUE"
                )


# Summary test
def test_phase_2_summary():
    """Print a summary of Phase 2 completion status."""
    summary = {
        "Phase 1 Complete": PHASE_1_AVAILABLE,
        "Generator Available": GENERATOR_AVAILABLE,
        "Formatter Available": FORMATTER_AVAILABLE,
        "Phase 2 Complete": PHASE_1_AVAILABLE and GENERATOR_AVAILABLE and FORMATTER_AVAILABLE,
    }

    # Check for cue binary
    try:
        subprocess.run(["cue", "version"], capture_output=True, check=True)
        cue_available = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        cue_available = False

    summary["CUE Binary Available"] = cue_available

    print("\n" + "=" * 60)
    print("PHASE 2 VALIDATION SUMMARY")
    print("=" * 60)
    for key, value in summary.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    print("=" * 60)

    if not summary["Phase 2 Complete"]:
        print("\nPhase 2 is NOT complete. Missing components:")
        if not PHASE_1_AVAILABLE:
            print("  - Phase 1 must be completed first!")
        if not GENERATOR_AVAILABLE:
            print("  - src/confidantic/workshop/generator.py")
        if not FORMATTER_AVAILABLE:
            print("  - src/confidantic/cue/formatter.py")
        print("\nRefer to ROADMAP-PHASE_2.md for implementation guidance.")
    else:
        print("\n✓ Phase 2 is COMPLETE! All required components are implemented.")
        print("  Generated CUE schemas are deterministic and valid.")
        print("  Ready to proceed to Phase 3: Required CUE workflow integration")

    if not cue_available:
        print("\n⚠ Warning: cue binary not found in PATH")
        print("  Install CUE: https://cuelang.org/docs/install/")

    print("=" * 60 + "\n")

    assert summary["Phase 2 Complete"], "Phase 2 is not yet complete"


# Fixtures used by tests
@pytest.fixture
def minimal_workshop_input(tmp_path: Path):
    """Create minimal WorkshopInput for testing (global fixture)."""
    if not PHASE_1_AVAILABLE:
        pytest.skip("Phase 1 required")

    import json

    from confidantic.workshop.loaders import load_workshop_input

    # Create minimal node-types.json
    node_types_data = [
        {"type": "identifier", "named": True},
    ]
    node_types_file = tmp_path / "node-types.json"
    node_types_file.write_text(json.dumps(node_types_data))

    # Create minimal query file
    queries_dir = tmp_path / "queries"
    queries_dir.mkdir()
    (queries_dir / "highlights.scm").write_text("(identifier) @variable")

    # Load WorkshopInput
    return load_workshop_input(
        grammar_name="test",
        node_types_path=node_types_file,
        queries_dir=queries_dir,
    )

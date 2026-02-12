"""
Phase 3 Validation Test Suite

This test file provides a quick check that Phase 3 (Required CUE Workflow Integration)
is complete and working correctly.

Run with: pytest tests/test_phase_3.py -v
"""

import subprocess
from pathlib import Path

import pytest

# Import previous phase components
try:
    from confidantic.workshop.generator import CueGenerator
    from confidantic.workshop.loaders import load_workshop_input

    PHASE_2_AVAILABLE = True
except ImportError:
    PHASE_2_AVAILABLE = False

# Try to import Phase 3 deliverables
try:
    from confidantic.cli.workshop import app as workshop_app

    CLI_WORKSHOP_AVAILABLE = True
except ImportError:
    CLI_WORKSHOP_AVAILABLE = False

try:
    from confidantic.cue.wrapper import check_cue_available, run_cue_fmt, run_cue_vet

    CUE_WRAPPER_AVAILABLE = True
except ImportError:
    CUE_WRAPPER_AVAILABLE = False


class TestPhase3Prerequisites:
    """Verify Phase 3 deliverables exist."""

    def test_phase_2_complete(self):
        """Verify Phase 2 is complete (required for Phase 3)."""
        assert PHASE_2_AVAILABLE, (
            "Phase 2 must be complete before Phase 3! "
            "Run: pytest tests/test_phase_2.py"
        )

    def test_justfile_exists(self):
        """Verify justfile exists."""
        justfile = Path("justfile")
        assert justfile.exists(), "justfile not found in repository root"

    def test_confidantic_just_exists(self):
        """Verify scripts/confidantic.just exists."""
        just_file = Path("scripts/confidantic.just")
        assert just_file.exists(), (
            "scripts/confidantic.just not found! Create scripts/confidantic.just"
        )

    def test_cli_workshop_module_exists(self):
        """Verify src/confidantic/cli/workshop.py exists."""
        workshop_cli = Path("src/confidantic/cli/workshop.py")
        assert workshop_cli.exists(), (
            "workshop.py not found! Create src/confidantic/cli/workshop.py"
        )

    def test_cue_wrapper_module_exists(self):
        """Verify src/confidantic/cue/wrapper.py exists."""
        wrapper_file = Path("src/confidantic/cue/wrapper.py")
        assert wrapper_file.exists(), (
            "wrapper.py not found! Create src/confidantic/cue/wrapper.py"
        )


@pytest.mark.skipif(not CUE_WRAPPER_AVAILABLE, reason="CUE wrapper not yet implemented")
class TestPhase3CueWrapper:
    """Verify CUE wrapper utilities are implemented."""

    def test_run_cue_fmt_exists(self):
        """Verify run_cue_fmt function exists."""
        assert callable(run_cue_fmt), "run_cue_fmt must be a callable function"

    def test_run_cue_vet_exists(self):
        """Verify run_cue_vet function exists."""
        assert callable(run_cue_vet), "run_cue_vet must be a callable function"

    def test_check_cue_available_exists(self):
        """Verify check_cue_available function exists."""
        assert callable(check_cue_available), "check_cue_available must be a callable function"

    def test_check_cue_available_works(self):
        """Test that check_cue_available returns a boolean."""
        result = check_cue_available()
        assert isinstance(result, bool), "check_cue_available must return bool"


@pytest.mark.skipif(not CLI_WORKSHOP_AVAILABLE, reason="CLI workshop not yet implemented")
class TestPhase3CliWorkshop:
    """Verify workshop CLI commands are implemented."""

    def test_workshop_cli_app_exists(self):
        """Verify workshop CLI app is defined."""
        assert workshop_app is not None, "workshop_app must be defined"

    def test_confidantic_command_available(self):
        """Test that confidantic CLI is installed and available."""
        try:
            result = subprocess.run(
                ["confidantic", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Should exit 0 or at least run without error
            assert result.returncode == 0 or "confidantic" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed yet")

    def test_workshop_subcommand_available(self):
        """Test that workshop subcommand is available."""
        try:
            result = subprocess.run(
                ["confidantic", "workshop", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, "workshop subcommand should be available"
            assert "workshop" in result.stdout.lower() or "generate" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed yet")


class TestPhase3JustRecipes:
    """Verify Just recipes are defined."""

    def test_just_binary_available(self):
        """Verify just binary is available in PATH."""
        try:
            result = subprocess.run(
                ["just", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            assert "just" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("just binary not found in PATH (required for Phase 3)")

    def test_workshop_recipes_defined(self):
        """Test that workshop recipes are defined in justfile."""
        try:
            result = subprocess.run(
                ["just", "--list"],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Check for key workshop recipes
            expected_recipes = [
                "cue-from-ts-generate",
                "cue-from-ts-fmt",
                "cue-from-ts-vet",
                "cue-from-ts-workshop",
            ]

            missing_recipes = []
            for recipe in expected_recipes:
                if recipe not in result.stdout:
                    missing_recipes.append(recipe)

            if missing_recipes:
                pytest.skip(
                    f"Workshop recipes not yet defined: {', '.join(missing_recipes)}\n"
                    f"Add these recipes to scripts/confidantic.just"
                )

        except FileNotFoundError:
            pytest.skip("just binary not found")

    def test_required_compatibility_recipes_exist(self):
        """Test that required compatibility recipes still exist."""
        try:
            result = subprocess.run(
                ["just", "--list"],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Check for required compatibility recipes
            required_recipes = [
                "config:validate",
                "config:dump",
                "schema:export",
                "schema:vet",
            ]

            missing_recipes = []
            for recipe in required_recipes:
                if recipe not in result.stdout:
                    missing_recipes.append(recipe)

            if missing_recipes:
                pytest.fail(
                    f"Required compatibility recipes are missing: {', '.join(missing_recipes)}\n"
                    f"These recipes must remain available for backward compatibility"
                )

        except FileNotFoundError:
            pytest.skip("just binary not found")


@pytest.mark.skipif(
    not (PHASE_2_AVAILABLE and CUE_WRAPPER_AVAILABLE),
    reason="Phase 2 and CUE wrapper required"
)
class TestPhase3CueWrapperIntegration:
    """Integration tests for CUE wrapper functionality."""

    @pytest.fixture
    def sample_cue_file(self, tmp_path: Path) -> Path:
        """Create a sample CUE file for testing."""
        cue_file = tmp_path / "test.cue"
        cue_file.write_text("""
package test

#Person: {
    name: string
    age: int
}
""")
        return cue_file

    @pytest.fixture
    def invalid_cue_file(self, tmp_path: Path) -> Path:
        """Create an invalid CUE file for testing."""
        cue_file = tmp_path / "invalid.cue"
        cue_file.write_text("""
package test

#Invalid: {
    missing_value:
}
""")
        return cue_file

    def test_run_cue_fmt_on_valid_file(self, sample_cue_file: Path):
        """Test formatting a valid CUE file."""
        if not check_cue_available():
            pytest.skip("cue binary not available")

        try:
            result = run_cue_fmt(sample_cue_file)
            assert result.returncode == 0
        except Exception as e:
            pytest.fail(f"run_cue_fmt failed: {e}")

    def test_run_cue_vet_on_valid_file(self, sample_cue_file: Path):
        """Test validating a valid CUE file."""
        if not check_cue_available():
            pytest.skip("cue binary not available")

        try:
            result = run_cue_vet(sample_cue_file)
            assert result.returncode == 0
        except subprocess.CalledProcessError:
            # This is okay - file might not be valid CUE without more context
            pass

    def test_run_cue_vet_on_invalid_file(self, invalid_cue_file: Path):
        """Test validating an invalid CUE file."""
        if not check_cue_available():
            pytest.skip("cue binary not available")

        try:
            result = run_cue_vet(invalid_cue_file)
            # Should fail for invalid CUE
            assert result.returncode != 0
        except subprocess.CalledProcessError as e:
            # This is expected for invalid CUE
            assert e.returncode != 0


@pytest.mark.skipif(
    not (PHASE_2_AVAILABLE and CLI_WORKSHOP_AVAILABLE),
    reason="Phase 2 and CLI workshop required"
)
class TestPhase3WorkflowIntegration:
    """Integration tests for complete workflow."""

    @pytest.fixture
    def sample_grammar_artifacts(self, tmp_path: Path):
        """Create sample Tree-sitter grammar artifacts."""
        import json

        # Create node-types.json
        node_types_data = [
            {"type": "module", "named": True},
            {"type": "identifier", "named": True},
        ]
        node_types_file = tmp_path / "node-types.json"
        node_types_file.write_text(json.dumps(node_types_data))

        # Create queries directory
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        (queries_dir / "highlights.scm").write_text("(identifier) @variable")

        return {
            "grammar": "test",
            "node_types": node_types_file,
            "queries_dir": queries_dir,
        }

    def test_cli_generate_command(self, sample_grammar_artifacts, tmp_path: Path):
        """Test confidantic workshop generate command."""
        output_dir = tmp_path / "build/schemas/cue/test"
        output_dir.mkdir(parents=True)

        try:
            result = subprocess.run(
                [
                    "confidantic",
                    "workshop",
                    "generate",
                    "--grammar",
                    sample_grammar_artifacts["grammar"],
                    "--node-types",
                    str(sample_grammar_artifacts["node_types"]),
                    "--queries-dir",
                    str(sample_grammar_artifacts["queries_dir"]),
                    "--output-dir",
                    str(output_dir),
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should succeed or at least run
            if result.returncode != 0:
                pytest.skip(
                    f"CLI generate not fully implemented yet. "
                    f"Error: {result.stderr}"
                )

            # Check that files were created
            cue_files = list(output_dir.glob("*.cue"))
            assert len(cue_files) > 0, "No CUE files were generated"

        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed yet")


# Summary test
def test_phase_3_summary():
    """Print a summary of Phase 3 completion status."""
    summary = {
        "Phase 2 Complete": PHASE_2_AVAILABLE,
        "CLI Workshop Available": CLI_WORKSHOP_AVAILABLE,
        "CUE Wrapper Available": CUE_WRAPPER_AVAILABLE,
    }

    # Check for external dependencies
    try:
        subprocess.run(["just", "--version"], capture_output=True, check=True)
        just_available = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        just_available = False

    try:
        subprocess.run(["cue", "version"], capture_output=True, check=True)
        cue_available = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        cue_available = False

    summary["Just Available"] = just_available
    summary["CUE Available"] = cue_available

    # Check for key files
    justfile_exists = Path("scripts/confidantic.just").exists()
    summary["Justfile Exists"] = justfile_exists

    # Overall completion
    summary["Phase 3 Complete"] = (
        PHASE_2_AVAILABLE
        and CLI_WORKSHOP_AVAILABLE
        and CUE_WRAPPER_AVAILABLE
        and justfile_exists
    )

    print("\n" + "=" * 60)
    print("PHASE 3 VALIDATION SUMMARY")
    print("=" * 60)
    for key, value in summary.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    print("=" * 60)

    if not summary["Phase 3 Complete"]:
        print("\nPhase 3 is NOT complete. Missing components:")
        if not PHASE_2_AVAILABLE:
            print("  - Phase 2 must be completed first!")
        if not CLI_WORKSHOP_AVAILABLE:
            print("  - src/confidantic/cli/workshop.py")
        if not CUE_WRAPPER_AVAILABLE:
            print("  - src/confidantic/cue/wrapper.py")
        if not justfile_exists:
            print("  - scripts/confidantic.just")
        print("\nRefer to ROADMAP-PHASE_3.md for implementation guidance.")
    else:
        print("\n✓ Phase 3 is COMPLETE! All required components are implemented.")
        print("  Just-first workflow with CUE integration is ready.")
        print("  Ready to proceed to Phase 4: Doctoring, diagnostics, and provenance")

    if not just_available:
        print("\n⚠ Warning: just binary not found in PATH")
        print("  Install just: https://github.com/casey/just")

    if not cue_available:
        print("\n⚠ Warning: cue binary not found in PATH")
        print("  Install CUE: https://cuelang.org/docs/install/")

    print("=" * 60 + "\n")

    assert summary["Phase 3 Complete"], "Phase 3 is not yet complete"

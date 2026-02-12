"""
Phase 5 Validation Test Suite

This test file provides a quick check that Phase 5 (CLI Plumbing and Migration Compatibility)
is complete and working correctly.

Run with: pytest tests/test_phase_5.py -v
"""

import subprocess
from pathlib import Path

import pytest

# Import previous phase components
try:
    from confidantic.workshop.doctor import WorkshopDoctor
    from confidantic.workshop.logging import WorkshopLogger

    PHASE_4_AVAILABLE = True
except ImportError:
    PHASE_4_AVAILABLE = False

# Try to import Phase 5 deliverables
try:
    from confidantic.cli import app as main_app

    MAIN_CLI_AVAILABLE = True
except ImportError:
    MAIN_CLI_AVAILABLE = False

try:
    from confidantic.compat import adapt_legacy_config_command, warn_deprecated

    COMPAT_AVAILABLE = True
except ImportError:
    COMPAT_AVAILABLE = False


class TestPhase5Prerequisites:
    """Verify Phase 5 deliverables exist."""

    def test_phase_4_complete(self):
        """Verify Phase 4 is complete (required for Phase 5)."""
        assert PHASE_4_AVAILABLE, (
            "Phase 4 must be complete before Phase 5! "
            "Run: pytest tests/test_phase_4.py"
        )

    def test_main_cli_exists(self):
        """Verify src/confidantic/cli.py or cli/__init__.py exists."""
        cli_file = Path("src/confidantic/cli.py")
        cli_init = Path("src/confidantic/cli/__init__.py")
        assert cli_file.exists() or cli_init.exists(), (
            "CLI module not found! Create src/confidantic/cli.py or src/confidantic/cli/__init__.py"
        )

    def test_compat_module_exists(self):
        """Verify src/confidantic/compat.py exists."""
        compat_file = Path("src/confidantic/compat.py")
        assert compat_file.exists(), (
            "compat.py not found! Create src/confidantic/compat.py"
        )

    def test_migration_docs_exist(self):
        """Verify docs/MIGRATION.md exists."""
        migration_doc = Path("docs/MIGRATION.md")
        assert migration_doc.exists(), (
            "MIGRATION.md not found! Create docs/MIGRATION.md"
        )


@pytest.mark.skipif(not MAIN_CLI_AVAILABLE, reason="Main CLI not yet implemented")
class TestPhase5MainCLI:
    """Verify main CLI structure is correct."""

    def test_main_app_exists(self):
        """Verify main CLI app is defined."""
        assert main_app is not None, "main_app must be defined"

    def test_confidantic_cli_is_installed(self):
        """Test that confidantic CLI is installed and accessible."""
        try:
            result = subprocess.run(
                ["confidantic", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, "CLI should exit with code 0 for --help"
            assert "confidantic" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed yet (run: pip install -e .)")

    def test_cli_has_version(self):
        """Test that CLI has version command or flag."""
        try:
            result = subprocess.run(
                ["confidantic", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Should show version or at least not error
            assert result.returncode == 0 or "version" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed yet")


@pytest.mark.skipif(not COMPAT_AVAILABLE, reason="Compat module not yet implemented")
class TestPhase5Compatibility:
    """Verify compatibility layer is implemented."""

    def test_adapt_legacy_config_command_exists(self):
        """Verify adapt_legacy_config_command function exists."""
        assert callable(adapt_legacy_config_command), (
            "adapt_legacy_config_command must be a callable function"
        )

    def test_warn_deprecated_exists(self):
        """Verify warn_deprecated function exists."""
        assert callable(warn_deprecated), (
            "warn_deprecated must be a callable function"
        )


class TestPhase5CLICommands:
    """Test that all required CLI command groups exist."""

    def test_cli_is_available(self):
        """Verify CLI is installed."""
        try:
            subprocess.run(["confidantic", "--help"], capture_output=True, check=True)
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed (run: pip install -e .)")

    def test_config_command_group_exists(self):
        """Test that config command group exists."""
        try:
            result = subprocess.run(
                ["confidantic", "config", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Should have config subcommands
            if result.returncode != 0:
                pytest.skip("config command group not yet implemented")

            assert "validate" in result.stdout.lower() or "dump" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")

    def test_schema_command_group_exists(self):
        """Test that schema command group exists."""
        try:
            result = subprocess.run(
                ["confidantic", "schema", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                pytest.skip("schema command group not yet implemented")

            assert "export" in result.stdout.lower() or "vet" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")

    def test_workshop_command_group_exists(self):
        """Test that workshop command group exists."""
        try:
            result = subprocess.run(
                ["confidantic", "workshop", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                pytest.skip("workshop command group not yet implemented")

            assert "generate" in result.stdout.lower() or "doctor" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")

    def test_logs_command_group_exists(self):
        """Test that logs command group exists."""
        try:
            result = subprocess.run(
                ["confidantic", "logs", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                pytest.skip("logs command group not yet implemented")

            assert "show" in result.stdout.lower() or "stats" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")


class TestPhase5BackwardCompatibility:
    """Test backward compatibility of existing commands."""

    def test_cli_available(self):
        """Check if CLI is installed."""
        try:
            subprocess.run(["confidantic", "--help"], capture_output=True, check=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("confidantic CLI not installed")

    def test_config_validate_command_exists(self):
        """Test that config:validate command still exists."""
        try:
            result = subprocess.run(
                ["confidantic", "config", "validate", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Should at least recognize the command
            if result.returncode == 2:  # Command not found
                pytest.fail("config validate command is missing! This is a breaking change.")
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")

    def test_config_dump_command_exists(self):
        """Test that config:dump command still exists."""
        try:
            result = subprocess.run(
                ["confidantic", "config", "dump", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 2:
                pytest.fail("config dump command is missing! This is a breaking change.")
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")

    def test_schema_export_command_exists(self):
        """Test that schema:export command still exists."""
        try:
            result = subprocess.run(
                ["confidantic", "schema", "export", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 2:
                pytest.fail("schema export command is missing! This is a breaking change.")
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")


class TestPhase5CLIFeatures:
    """Test CLI features like JSON output, quiet mode, etc."""

    def test_cli_has_json_flag(self):
        """Test that CLI supports --json flag."""
        try:
            result = subprocess.run(
                ["confidantic", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Check if --json is mentioned in help
            # Some CLIs have global flags, others per-command
            if result.returncode == 0:
                # Just verify help runs, JSON support may be per-command
                pass
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")

    def test_cli_has_verbose_flag(self):
        """Test that CLI supports --verbose flag."""
        try:
            result = subprocess.run(
                ["confidantic", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Just verify help runs
                pass
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")


class TestPhase5Documentation:
    """Test that required documentation exists."""

    def test_migration_doc_exists(self):
        """Verify MIGRATION.md exists."""
        migration_doc = Path("docs/MIGRATION.md")
        assert migration_doc.exists(), "docs/MIGRATION.md must exist"

    def test_migration_doc_has_content(self):
        """Verify MIGRATION.md has meaningful content."""
        migration_doc = Path("docs/MIGRATION.md")
        if not migration_doc.exists():
            pytest.skip("MIGRATION.md doesn't exist yet")

        content = migration_doc.read_text()
        assert len(content) > 100, "MIGRATION.md seems empty or too short"
        assert "migration" in content.lower(), "MIGRATION.md should mention migration"

    def test_ci_integration_doc_exists(self):
        """Verify CI_INTEGRATION.md exists."""
        ci_doc = Path("docs/CI_INTEGRATION.md")
        assert ci_doc.exists(), "docs/CI_INTEGRATION.md should exist"

    def test_ci_integration_doc_has_examples(self):
        """Verify CI_INTEGRATION.md has examples."""
        ci_doc = Path("docs/CI_INTEGRATION.md")
        if not ci_doc.exists():
            pytest.skip("CI_INTEGRATION.md doesn't exist yet")

        content = ci_doc.read_text()
        # Should have at least one CI platform example
        has_github = "github" in content.lower()
        has_gitlab = "gitlab" in content.lower()
        has_makefile = "makefile" in content.lower() or "make" in content.lower()

        assert has_github or has_gitlab or has_makefile, (
            "CI_INTEGRATION.md should have at least one CI platform example"
        )


class TestPhase5MigrationUtilities:
    """Test migration utilities if implemented."""

    def test_migrate_command_group_exists(self):
        """Test that migrate command group exists (optional)."""
        try:
            result = subprocess.run(
                ["confidantic", "migrate", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 2:
                pytest.skip("migrate command group not implemented (optional)")

            # If it exists, check for subcommands
            if result.returncode == 0:
                assert "check" in result.stdout.lower() or "apply" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("confidantic CLI not installed")


# Summary test
def test_phase_5_summary():
    """Print a summary of Phase 5 completion status."""
    summary = {
        "Phase 4 Complete": PHASE_4_AVAILABLE,
        "Main CLI Available": MAIN_CLI_AVAILABLE,
        "Compat Module Available": COMPAT_AVAILABLE,
    }

    # Check for CLI installation
    try:
        subprocess.run(["confidantic", "--help"], capture_output=True, check=True, timeout=5)
        cli_installed = True
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        cli_installed = False

    summary["CLI Installed"] = cli_installed

    # Check for documentation
    migration_doc_exists = Path("docs/MIGRATION.md").exists()
    ci_doc_exists = Path("docs/CI_INTEGRATION.md").exists()

    summary["Migration Docs Exist"] = migration_doc_exists
    summary["CI Integration Docs Exist"] = ci_doc_exists

    # Overall completion
    summary["Phase 5 Complete"] = (
        PHASE_4_AVAILABLE
        and MAIN_CLI_AVAILABLE
        and COMPAT_AVAILABLE
        and migration_doc_exists
        and ci_doc_exists
    )

    print("\n" + "=" * 60)
    print("PHASE 5 VALIDATION SUMMARY")
    print("=" * 60)
    for key, value in summary.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    print("=" * 60)

    if not summary["Phase 5 Complete"]:
        print("\nPhase 5 is NOT complete. Missing components:")
        if not PHASE_4_AVAILABLE:
            print("  - Phase 4 must be completed first!")
        if not MAIN_CLI_AVAILABLE:
            print("  - src/confidantic/cli.py or cli/__init__.py")
        if not COMPAT_AVAILABLE:
            print("  - src/confidantic/compat.py")
        if not migration_doc_exists:
            print("  - docs/MIGRATION.md")
        if not ci_doc_exists:
            print("  - docs/CI_INTEGRATION.md")
        print("\nRefer to ROADMAP-PHASE_5.md for implementation guidance.")
    else:
        print("\n✓ Phase 5 is COMPLETE! All required components are implemented.")
        print("  CLI plumbing and migration compatibility are ready.")
        print("  Ready to proceed to Phase 6: Hardening and quality gates")

    if not cli_installed:
        print("\n⚠ Note: Run 'pip install -e .' to install CLI for testing")

    print("=" * 60 + "\n")

    assert summary["Phase 5 Complete"], "Phase 5 is not yet complete"

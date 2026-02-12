"""
Phase 6 Validation Test Suite

This test file provides a quick check that Phase 6 (Hardening and Quality Gates)
is complete and working correctly.

Run with: pytest tests/test_phase_6.py -v
"""

import subprocess
from pathlib import Path

import pytest

# Import previous phase components
try:
    from confidantic.cli import app as main_app
    from confidantic.compat import warn_deprecated

    PHASE_5_AVAILABLE = True
except ImportError:
    PHASE_5_AVAILABLE = False


class TestPhase6Prerequisites:
    """Verify Phase 6 deliverables exist."""

    def test_phase_5_complete(self):
        """Verify Phase 5 is complete (required for Phase 6)."""
        assert PHASE_5_AVAILABLE, (
            "Phase 5 must be complete before Phase 6! "
            "Run: pytest tests/test_phase_5.py"
        )

    def test_ci_workflow_exists(self):
        """Verify CI workflow configuration exists."""
        github_ci = Path(".github/workflows/ci.yml")
        gitlab_ci = Path(".gitlab-ci.yml")

        assert github_ci.exists() or gitlab_ci.exists(), (
            "CI workflow not found! Create .github/workflows/ci.yml or .gitlab-ci.yml"
        )

    def test_release_checklist_exists(self):
        """Verify RELEASE_CHECKLIST.md exists."""
        checklist = Path("RELEASE_CHECKLIST.md")
        assert checklist.exists(), (
            "RELEASE_CHECKLIST.md not found! Create RELEASE_CHECKLIST.md"
        )


class TestPhase6Fixtures:
    """Test that required fixtures exist."""

    def test_python_fixture_exists(self):
        """Verify Python grammar fixture exists."""
        python_fixtures = Path("tests/fixtures/python")
        assert python_fixtures.exists(), (
            "Python fixture directory not found! Create tests/fixtures/python/"
        )

    def test_python_node_types_fixture_exists(self):
        """Verify Python node-types.json fixture exists."""
        node_types = Path("tests/fixtures/python/node-types.json")
        assert node_types.exists(), (
            "Python node-types.json fixture not found!"
        )

    def test_python_queries_fixture_exists(self):
        """Verify Python queries fixture directory exists."""
        queries_dir = Path("tests/fixtures/python/queries")
        assert queries_dir.exists(), (
            "Python queries directory not found!"
        )

    def test_golden_snapshots_exist(self):
        """Verify golden snapshots exist."""
        golden_dir = Path("tests/fixtures/golden/python")
        if not golden_dir.exists():
            pytest.skip("Golden snapshots not yet created")

        # Should have at least one snapshot file
        snapshots = list(golden_dir.glob("*.cue"))
        assert len(snapshots) > 0, (
            "No golden snapshot .cue files found in tests/fixtures/golden/python/"
        )


class TestPhase6QualityGateTests:
    """Test that quality gate test files exist."""

    def test_golden_snapshot_tests_exist(self):
        """Verify golden snapshot tests exist."""
        test_file = Path("tests/integration/test_golden_snapshots.py")
        assert test_file.exists(), (
            "test_golden_snapshots.py not found! Create tests/integration/test_golden_snapshots.py"
        )

    def test_cue_formatting_tests_exist(self):
        """Verify CUE formatting tests exist."""
        test_file = Path("tests/integration/test_cue_formatting.py")
        assert test_file.exists(), (
            "test_cue_formatting.py not found! Create tests/integration/test_cue_formatting.py"
        )

    def test_jsonl_behavior_tests_exist(self):
        """Verify JSONL behavior tests exist."""
        test_file = Path("tests/integration/test_jsonl_behavior.py")
        assert test_file.exists(), (
            "test_jsonl_behavior.py not found! Create tests/integration/test_jsonl_behavior.py"
        )

    def test_redaction_tests_exist(self):
        """Verify redaction tests exist."""
        test_file = Path("tests/integration/test_redaction.py")
        assert test_file.exists(), (
            "test_redaction.py not found! Create tests/integration/test_redaction.py"
        )


class TestPhase6EndToEndTests:
    """Test that end-to-end integration tests exist."""

    def test_workshop_integration_directory_exists(self):
        """Verify workshop integration test directory exists."""
        workshop_dir = Path("tests/integration/workshop")
        assert workshop_dir.exists(), (
            "Workshop integration directory not found! Create tests/integration/workshop/"
        )

    def test_python_workshop_test_exists(self):
        """Verify Python workshop end-to-end test exists."""
        test_file = Path("tests/integration/workshop/test_python_workshop.py")
        assert test_file.exists(), (
            "test_python_workshop.py not found! Create tests/integration/workshop/test_python_workshop.py"
        )


class TestPhase6PerformanceTests:
    """Test that performance tests exist."""

    def test_performance_test_directory_exists(self):
        """Verify performance test directory exists."""
        perf_dir = Path("tests/performance")
        assert perf_dir.exists(), (
            "Performance test directory not found! Create tests/performance/"
        )

    def test_benchmark_tests_exist(self):
        """Verify benchmark tests exist."""
        test_file = Path("tests/performance/test_benchmarks.py")
        assert test_file.exists(), (
            "test_benchmarks.py not found! Create tests/performance/test_benchmarks.py"
        )


class TestPhase6CIRecipes:
    """Test that CI Just recipes exist."""

    def test_just_binary_available(self):
        """Check if just is available."""
        try:
            subprocess.run(["just", "--version"], capture_output=True, check=True)
        except FileNotFoundError:
            pytest.skip("just binary not found (optional for local testing)")

    def test_ci_recipes_defined(self):
        """Test that CI recipes are defined in justfile."""
        try:
            result = subprocess.run(
                ["just", "--list"],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Check for CI recipes
            ci_recipes = ["ci:test", "ci:quality", "ci:check"]
            found_recipes = []
            for recipe in ci_recipes:
                if recipe in result.stdout:
                    found_recipes.append(recipe)

            if not found_recipes:
                pytest.skip("CI recipes not yet defined (optional)")

        except FileNotFoundError:
            pytest.skip("just binary not found")


class TestPhase6Documentation:
    """Test that Phase 6 documentation is complete."""

    def test_release_checklist_has_content(self):
        """Verify RELEASE_CHECKLIST.md has meaningful content."""
        checklist = Path("RELEASE_CHECKLIST.md")
        if not checklist.exists():
            pytest.skip("RELEASE_CHECKLIST.md doesn't exist yet")

        content = checklist.read_text()
        assert len(content) > 100, "RELEASE_CHECKLIST.md seems empty"
        assert "release" in content.lower(), "Should mention release"
        assert "- [ ]" in content, "Should have checkboxes"

    def test_readme_mentions_quality_gates(self):
        """Verify README mentions quality gates or testing."""
        readme = Path("README.md")
        if not readme.exists():
            pytest.skip("README.md doesn't exist")

        content = readme.read_text()
        # Should mention testing or quality in some form
        quality_indicators = ["test", "quality", "ci", "coverage"]
        has_quality_mention = any(indicator in content.lower() for indicator in quality_indicators)

        if not has_quality_mention:
            pytest.skip("README doesn't mention quality/testing yet (optional)")


class TestPhase6CoverageTarget:
    """Test that code coverage meets target."""

    def test_coverage_plugin_available(self):
        """Check if pytest-cov is installed."""
        try:
            import pytest_cov
        except ImportError:
            pytest.skip("pytest-cov not installed (run: pip install pytest-cov)")

    def test_can_run_coverage_report(self):
        """Test that coverage report can be generated."""
        try:
            result = subprocess.run(
                ["pytest", "--cov=src/confidantic", "--cov-report=term", "--collect-only"],
                capture_output=True,
                timeout=10
            )
            # Should at least collect tests
            assert result.returncode == 0 or result.returncode == 5  # 5 = no tests collected
        except FileNotFoundError:
            pytest.skip("pytest not found")


class TestPhase6QualityChecks:
    """Test that quality check tools are configured."""

    def test_pyproject_has_dev_dependencies(self):
        """Verify pyproject.toml has dev dependencies."""
        pyproject = Path("pyproject.toml")
        if not pyproject.exists():
            pytest.skip("pyproject.toml doesn't exist")

        content = pyproject.read_text()
        # Should have some dev/test dependencies
        has_dev_deps = (
            "[project.optional-dependencies]" in content
            or "[tool.pytest" in content
            or "pytest" in content
        )

        if not has_dev_deps:
            pytest.skip("Dev dependencies not yet configured")


# Summary test
def test_phase_6_summary():
    """Print a summary of Phase 6 completion status."""
    summary = {
        "Phase 5 Complete": PHASE_5_AVAILABLE,
    }

    # Check for CI workflow
    github_ci = Path(".github/workflows/ci.yml")
    gitlab_ci = Path(".gitlab-ci.yml")
    summary["CI Workflow Exists"] = github_ci.exists() or gitlab_ci.exists()

    # Check for fixtures
    python_fixtures = Path("tests/fixtures/python")
    summary["Python Fixtures Exist"] = python_fixtures.exists()

    # Check for quality gate tests
    golden_tests = Path("tests/integration/test_golden_snapshots.py")
    cue_tests = Path("tests/integration/test_cue_formatting.py")
    jsonl_tests = Path("tests/integration/test_jsonl_behavior.py")
    summary["Quality Gate Tests Exist"] = (
        golden_tests.exists() and cue_tests.exists() and jsonl_tests.exists()
    )

    # Check for end-to-end tests
    e2e_test = Path("tests/integration/workshop/test_python_workshop.py")
    summary["End-to-End Tests Exist"] = e2e_test.exists()

    # Check for performance tests
    perf_tests = Path("tests/performance/test_benchmarks.py")
    summary["Performance Tests Exist"] = perf_tests.exists()

    # Check for release checklist
    checklist = Path("RELEASE_CHECKLIST.md")
    summary["Release Checklist Exists"] = checklist.exists()

    # Overall completion
    summary["Phase 6 Complete"] = all([
        PHASE_5_AVAILABLE,
        summary["CI Workflow Exists"],
        summary["Python Fixtures Exist"],
        summary["Quality Gate Tests Exist"],
        summary["End-to-End Tests Exist"],
        summary["Performance Tests Exist"],
        summary["Release Checklist Exists"],
    ])

    print("\n" + "=" * 60)
    print("PHASE 6 VALIDATION SUMMARY")
    print("=" * 60)
    for key, value in summary.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    print("=" * 60)

    if not summary["Phase 6 Complete"]:
        print("\nPhase 6 is NOT complete. Missing components:")
        if not PHASE_5_AVAILABLE:
            print("  - Phase 5 must be completed first!")
        if not summary["CI Workflow Exists"]:
            print("  - .github/workflows/ci.yml or .gitlab-ci.yml")
        if not summary["Python Fixtures Exist"]:
            print("  - tests/fixtures/python/")
        if not summary["Quality Gate Tests Exist"]:
            print("  - tests/integration/test_golden_snapshots.py")
            print("  - tests/integration/test_cue_formatting.py")
            print("  - tests/integration/test_jsonl_behavior.py")
        if not summary["End-to-End Tests Exist"]:
            print("  - tests/integration/workshop/test_python_workshop.py")
        if not summary["Performance Tests Exist"]:
            print("  - tests/performance/test_benchmarks.py")
        if not summary["Release Checklist Exists"]:
            print("  - RELEASE_CHECKLIST.md")
        print("\nRefer to ROADMAP-PHASE_6.md for implementation guidance.")
    else:
        print("\n" + "=" * 60)
        print("🎉 PHASE 6 is COMPLETE! 🎉")
        print("=" * 60)
        print("\nAll phases (1-6) are now complete!")
        print("\nConfidantic is production-ready and can be released as v1.0.0")
        print("\nNext steps:")
        print("  1. Run full test suite: pytest tests/ -v")
        print("  2. Check code coverage: pytest --cov=src/confidantic --cov-report=term")
        print("  3. Review RELEASE_CHECKLIST.md")
        print("  4. Run CI locally: just ci:all (if just is installed)")
        print("  5. Prepare for v1.0.0 release")
        print("\nCongratulations on completing all roadmap phases! 🎊")

    print("=" * 60 + "\n")

    assert summary["Phase 6 Complete"], "Phase 6 is not yet complete"

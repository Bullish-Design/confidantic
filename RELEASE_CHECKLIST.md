# Release Readiness Checklist

Use this checklist before each release to ensure quality and completeness.

## Code Quality

- [ ] All tests pass (`pytest tests/`)
- [ ] Code coverage ≥ 90% (`pytest --cov`)
- [ ] No critical lint/type errors
- [ ] No known high/critical vulnerabilities

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
- [ ] CHANGELOG updated
- [ ] Version bumped

## CI/CD

- [ ] Phase-6 Python CI script passes (`python scripts/ci/phase6_quality_gates.py all`)
- [ ] All quality gates pass
- [ ] Tests run on Python 3.11, 3.12, 3.13

## Backward Compatibility

- [ ] All existing commands work
- [ ] No breaking changes (or documented)
- [ ] Migration path provided (if needed)

## Release Process

- [ ] Tag created (`vX.Y.Z`)
- [ ] Changelog entry added
- [ ] Release artifact published
- [ ] Announcement posted

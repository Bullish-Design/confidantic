# CI Integration

Confidantic CI should call Python CLI workflow commands directly.

## Required tools on PATH

- `tree-sitter`
- `cue`
- `jq`
- `confidantic`
- `confidantic-cue`

## Baseline command sequence

```bash
confidantic config validate
confidantic workflow doctor python
confidantic workflow generate python
confidantic workflow fmt python
confidantic workflow vet python
```

## Makefile example

```make
CONFIDANTIC_ROOT ?= $(CURDIR)/.devman/.config
GRAMMAR ?= python

.PHONY: confidantic-bootstrap confidantic-workflow

confidantic-bootstrap:
	@mkdir -p "$(CONFIDANTIC_ROOT)"

confidantic-workflow: confidantic-bootstrap
	@CONFIDANTIC_ROOT="$(CONFIDANTIC_ROOT)" confidantic workflow workshop $(GRAMMAR)
```

## Phase 6 runner

```bash
python scripts/ci/phase6_quality_gates.py all
```

# Python Tree-sitter Fixture

This fixture contains representative Python Tree-sitter artifacts used for end-to-end workshop and golden snapshot tests.

## Contents

- `node-types.json` — node type definitions from Python grammar output
- `queries/highlights.scm` — highlight capture queries
- `queries/tags.scm` — tag/navigation queries
- `../golden/python/*.cue` — deterministic expected CUE outputs

## Update process

1. Refresh `node-types.json` and query files from the desired Tree-sitter Python revision.
2. Regenerate CUE outputs using:
   - `confidantic workshop generate --grammar python --node-types tests/fixtures/python/node-types.json --queries-dir tests/fixtures/python/queries --output-dir build/schemas/cue/python`
3. Copy generated files into `tests/fixtures/golden/python/`.
4. Re-run snapshot and integration tests.

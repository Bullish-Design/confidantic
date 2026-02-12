# Workshop JSONL Log Format

All workshop operations append structured events to `logs/workshop.jsonl`.

## Event schema

Each line is a standalone JSON object:

- `timestamp` (ISO8601 UTC)
- `stage` (`load|generate|fmt|vet|test|doctor`)
- `status` (`started|success|failure`)
- `grammar` (optional)
- `artifact_paths` (optional array of paths)
- `error` (optional string)
- `duration_ms` (optional float)
- `metadata` (optional object)
- `agent_id` / `session_id` / `user_id` (optional)

## Append-only contract

- One event per line
- UTF-8 encoding
- Events are written with file locking to prevent concurrent-write corruption
- Invalid lines are skipped by readers with warnings

## CLI commands

- `confidantic logs show` supports `--grammar`, `--stage`, `--status`, `--failures-only`, and `--limit`.
- `confidantic logs stats` emits aggregate counts and stage duration summaries.
- `confidantic logs query` supports explicit predicates with `--grammar`, `--stage`, `--status`, `--since`, `--until`, and `--window`.
- All logs commands support deterministic machine output via `--format json`/`--format jsonl` or `--json`.

## jq examples

```bash
# failures only
jq 'select(.status=="failure")' logs/workshop.jsonl

# events for one grammar
jq 'select(.grammar=="python")' logs/workshop.jsonl

# average duration by stage
jq -s 'group_by(.stage) | map({stage: .[0].stage, avg_ms: (map(.duration_ms // 0) | add / length)})' logs/workshop.jsonl
```

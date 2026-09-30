# FirmFlow collector

Finds what new hires struggle with by reading **new** messages from a small, explicit
list of help channels, anonymizing them **locally**, and sending only anonymized
aggregates to the FirmFlow backend. It runs inside the firm's own environment.

## Privacy rules this code enforces

- **Allowlist only.** A connector refuses any channel not listed in the config, and
  rejects any message that doesn't belong to the channel it was asked for. No wildcards.
- **Authors are pseudonymized at the edge.** `Message.author_hash` must come from
  `hash_author()` (HMAC with a secret salt kept in the environment). Raw ids, names, and
  emails are rejected by the model.
- **Cursors stay local** in a SQLite file. The backend never learns what was read.
- **Secrets come from the environment**, never the config file.
- **Minimum group size** (default 5, floor 3): no topic may describe fewer people.

## Status

| Piece | State |
|---|---|
| Message schema, connector interface, allowlist enforcement | done, tested |
| Local cursor store, incremental ingest | done, tested |
| Config and `check-config` command | done, tested |
| Synthetic data, redaction, analysis, publishing, real connectors | later phases |

## Try it

```
cd collector
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
export COLLECTOR_AUTHOR_SALT="$(openssl rand -hex 16)"
python -m collector check-config config.example.yaml
```

## Writing a connector

Subclass `Connector`, set `source`, and implement `_fetch_new(channel, cursor, *, since, limit)`
returning a `FetchResult(messages, cursor, has_more)`. Call `fetch_new` (not `_fetch_new`)
from outside: it enforces the allowlist and checks your output. The cursor is opaque to
everything else. `since` bounds the first run only.

Ingest is at-least-once: the cursor moves only after the handler accepts a page, so handlers
should tolerate seeing a message twice.

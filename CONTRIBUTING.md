# Contributing

## Setup

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

Tests need no API key and make no network requests, except that tiktoken downloads its `cl100k_base` encoding the first time it runs on a machine.

## Recorded Jev responses

`tests/test_end_to_end.py` replays the Jev responses recorded in `tests/fixtures/e2e/jev`, keyed by the hash of each request. A change to extraction, prompts, thresholds, or the text sent to Jev changes the requests, and the test then fails with "no recorded Jev response". Re-recording needs a TypeSafe API key:

```bash
JEVFETCH_RECORD=1 uv run pytest tests/test_end_to_end.py
```

CI has no key, so a pull request from a fork cannot re-record. Open the pull request with the failing test and say so in the description; a maintainer re-records and adds the fixtures to the branch.

## Pull requests

Pull requests are squash-merged, so the pull request title becomes the commit on `main` and the commits on your branch do not. Write the title as one line in the form `type: description`, with type one of feat, fix, docs, refactor, test, chore. Details belong in the pull request description.

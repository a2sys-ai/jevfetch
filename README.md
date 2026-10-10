# jevfetch

**Use it instead of WebFetch: agent runs take 30 to 32% less time and cost 42 to 43% less (compared with WebFetch on Haiku 4.5).**

[![ci](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml/badge.svg)](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

[한국어](README.ko.md) · [Quick start](#quick-start) · [Command-line use](#command-line-use) · [Python API](#python-api) · [More agent setup](#more-agent-setup)

## Why jevfetch

| Approach | What the agent gets | Good for |
|---|---|---|
| Fetch the whole page | The full extracted text | Summaries, translations |
| A small model answers from the page (WebFetch) | A paraphrase, without the source text | Questions that don't need the page's exact wording |
| jevfetch | Passages quoted verbatim, with their heading paths | Looking up a specific fact on a long page |

Passing the whole page eats context and costs more. A paraphrase can't be quoted or checked against the page.

jevfetch splits the page into blocks and asks TypeSafe's judgment model [Jev](https://docs.typesafe.ai) whether each block answers the question. It returns only the blocks that do, exactly as they appear on the page.

We compared it with Claude Code's WebFetch on 32 documentation questions, giving the page URL with each question and running every question twice in Korean and twice in English:

| Compared with | Agent time | Cost |
|---|---|---|
| WebFetch (Haiku 4.5) | 30 to 32% less | 42 to 43% less |
| WebFetch (Haiku 5.5) | 42 to 47% less | 3 to 13% less |

Out of 126 checks per language for facts the answer must contain, jevfetch passed 124 and WebFetch (Haiku 5.5) passed all 126. For English questions, the cost difference against Haiku 5.5 is within the margin of error. Full conditions and limits are in [bench/RESULTS.md](bench/RESULTS.md).

## Example

```bash
jevfetch https://docs.python.org/3/library/functools.html "What happens if lru_cache maxsize is None?"
```

Output (trimmed):

```text
# jevfetch: https://docs.python.org/3/library/functools.html
# status: filtered (blocks are quoted from the page; '##' lines are the page's heading path)
# 8/133 blocks, 461 of 7141 tokens
## functools — Higher-order functions and operations on callable objects
Source code: [Lib/functools.py](https://github.com/python/cpython/tree/3.14/Lib/functools.py)
## functools — Higher-order functions and operations on callable objects > @functools.lru_cache(maxsize=128, typed=False)
Decorator to wrap a function with a memoizing callable that saves up to the maxsize most recent calls. ...
If maxsize is set to None, the LRU feature is disabled and the cache can grow without bound.
...
```

> [!NOTE]
> The agent gets 461 of the page's 7,141 tokens. This call used 37,327 Jev input tokens (about $0.0015) with an empty cache.

Each `##` line is the heading path of the passage below it. Definition-list terms such as function signatures are part of the path, so the agent can tell that the sentence about `maxsize=None` belongs to `lru_cache`.

The text is copied from the page. The only changes jevfetch makes are:

- collapsing runs of whitespace
- writing links as `[text](url)`
- separating table cells with ` | `
- adding `- ` before list items merged into one block
- adding the `##` lines

JSON and XML are re-serialized, so whitespace, escapes, and number notation in those blocks can differ from the source. For example, `1.10` prints as `1.1`.

## Quick start

The jevfetch skill installs into Claude Code, Codex, and many other coding agents with the [skills](https://github.com/vercel-labs/skills) CLI. These steps are for Claude Code. You need [uv](https://docs.astral.sh/uv/), Node.js (for `npx`), and a [TypeSafe](https://typesafe.ai) API key (see [API key](#api-key)).

1. Install the [jevfetch skill](skills/jevfetch/SKILL.md) in your project. The skill tells Claude Code to read web pages with jevfetch, including pages it found with WebSearch, and what to do with each status. Without it, Claude Code keeps using WebFetch.

   ```bash
   npx skills add a2sys-ai/jevfetch --skill jevfetch -a claude-code
   ```

2. Let jevfetch run without a permission prompt. Add this to `.claude/settings.json` in your project. If the file already exists, just add the entry to `permissions.allow`.

   ```json
   {
     "permissions": {
       "allow": ["Bash(jevfetch:*)"]
     }
   }
   ```

### API key

Add your API key to your shell profile (`~/.bashrc` for bash). Then open a new terminal and start Claude Code from it.

```bash
echo 'export TYPESAFE_API_KEY=<your key>' >> ~/.zshrc
```

Now open Claude Code in that project and ask something that needs a look at the docs. If the `jevfetch` command is missing, Claude Code installs it the first time, and asks before doing so unless your settings already allow it.

To set up other agents, install without Node.js, or turn WebFetch off, see [More agent setup](#more-agent-setup).

## Command-line use

With the skill, jevfetch gets installed automatically when it's needed. To install it yourself (Python 3.12 or later):

```bash
uv tool install git+https://github.com/a2sys-ai/jevfetch@v0.1.0
```

Chrome or Chromium is optional. If present, it's used for pages that load their content with JavaScript.

Run it with a URL and a question, as in the [example](#example). The `#` lines at the top of the output report the status:

| Status | Meaning | Exit code |
|---|---|---|
| `filtered` | Blocks above the threshold, plus the first block. If the blocks other than the first add up to fewer than 300 tokens, the next highest-scoring blocks are added | 0 |
| `passthrough` | The page is 2,000 tokens or less, so it is returned whole | 0 |
| `no_match` | No block passed the threshold, so the highest-scoring blocks are returned. The answer may still be on the page | 0 |
| `empty` | No text could be extracted | 0 |
| `fetch_error` | The page could not be fetched, or the URL is a PDF, image, or other binary file. For a binary file, the error shows the content type and a `# saved:` line gives the path of the downloaded file | 1 |

If a Jev request fails (missing key, no credits), jevfetch exits with code 2.

Options:

- `--json`: print the result as JSON, with token counts and Jev usage
- `--no-render`: don't fall back to a headless browser
- `--model`: set the Jev model

The command takes a URL. For HTML, Markdown, or plain text you already have, use the [Python API](#python-api). jevfetch doesn't pick passages from PDFs and other binary files. Like WebFetch, it saves them and prints the path, so the agent can open them with its file reader.

## More agent setup

The [skills](https://github.com/vercel-labs/skills) installer works with Claude Code, Codex, and many other coding agents, and needs Node.js. By default it installs into the current project. Add `-g` to install it for all your projects, and use `-a <agent>` to pick the agents.

<details>
<summary>Install without Node.js</summary>

Download the skill file for Claude Code yourself. To use it in one project only, put it in that project's `.claude/skills/` instead of `~/.claude/skills/`.

```bash
mkdir -p ~/.claude/skills/jevfetch
curl -fsSL https://raw.githubusercontent.com/a2sys-ai/jevfetch/main/skills/jevfetch/SKILL.md -o ~/.claude/skills/jevfetch/SKILL.md
```

</details>

### Turning WebFetch off

With WebFetch off, Claude Code reads every page with jevfetch. Add a deny rule to `.claude/settings.json` in the project, or to `.claude/settings.local.json` to apply it only to yourself. For a single session, start Claude Code with `--disallowedTools WebFetch`.

```json
{
  "permissions": {
    "deny": ["WebFetch"]
  }
}
```

PDFs and other files still reach the agent: jevfetch saves them, and the agent opens the saved file with Read. jevfetch doesn't summarize whole pages, though, so keep WebFetch on in projects that need that.

### Codex

Codex CLI and the Codex IDE extension block network access for commands by default, so both the first install and every jevfetch call fail until you allow it. Add this to `~/.codex/config.toml`:

```toml
[sandbox_workspace_write]
network_access = true
```

### Agents without skill support

Add these lines to the agent's instruction file (`AGENTS.md`, `CLAUDE.md`, and so on):

```
To get a specific fact from a web page, including pages found by web search, run `jevfetch <url> "<question>"` instead of fetching the whole page.
Its output is quoted from the page, so there is no need to fetch the page again to check it.
If the status is no_match, ask a more specific question or try another page. For a PDF or another file, jevfetch prints a `# saved:` line; open that file with your file reader.
```

## When to use it

jevfetch is built for looking up specific facts on long pages: documentation, references, Wikipedia.

Use something else when:

- The task needs the whole page, like a summary or translation. jevfetch returns only parts of the page.
- The pages are short. Pages of 2,000 tokens or less come back whole, so you get nothing over fetching the page.
- The URL is a PDF, image, or other binary file. jevfetch only picks passages from HTML and text formats such as Markdown, JSON, and XML. For binary files it returns `fetch_error` with the content type, without calling Jev, and saves the file so the agent can open it with Read.

## Privacy and security

- jevfetch sends the page text and your question to the TypeSafe API.
- The first time jevfetch runs on a machine, tiktoken downloads its `cl100k_base` encoding from `openaipublic.blob.core.windows.net` and caches it locally.
- Jev responses are cached in `~/.cache/jevfetch` (change it with `JEVFETCH_CACHE_DIR`). The cache is safe to delete.
- PDFs and other binary files are saved in a `jevfetch-<uid>` folder in the system's temporary directory (change it with `JEVFETCH_FILES_DIR`).

> [!WARNING]
> jevfetch fetches any URL it is given and follows redirects. If you run it as a service, restrict which URLs it can fetch.

## How it works

1. Fetch the page. If the static HTML has less than 200 tokens of text, render it in headless Chrome.
2. Split the page into blocks, tag each with its heading path, and drop navigation, footers, and other page chrome. A sentence ending in a colon is merged with the list items that follow it under the same heading, up to 1,500 characters, so that a condition it states stays with the items. JSON is split by key and array item, and XML by element, with the key or tag path in place of the heading path.
3. Return documents of 2,000 tokens or less as they are.
4. First pass: group blocks into windows of about 3,000 tokens and send one Jev request per window, asking yes or no for each block. Blocks scoring 0.3 or higher become candidates.
5. Second pass: ask about each candidate again on its own, with up to 400 characters from each neighboring block as context. Keep blocks scoring 0.8 or higher.
6. Always keep the first block, since its heading path usually contains the page title. If the other kept blocks add up to fewer than 300 tokens, add the highest-scoring remaining blocks.

Requests within each pass run concurrently.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `TYPESAFE_API_KEY` | none | Jev API key. Not needed if every request is served from the cache |
| `JEVFETCH_CACHE_DIR` | `~/.cache/jevfetch` | Jev response cache directory |
| `JEVFETCH_FILES_DIR` | `jevfetch-<uid>` in the system's temporary directory | Directory for saved PDFs and other binary files |
| `JEVFETCH_CHROME` | auto-detected | Chrome or Chromium binary for rendering |
| `JEVFETCH_USER_AGENT` | jevfetch name, version, and repository URL | User-Agent header for page requests |

The default model is the alias `jev-latest`, and the cache is keyed by that name, so after a model update the cache can still return answers from the previous model. For reproducible results, pin a model version with `--model` or `Config(model=...)`.

## Python API

```python
from jevfetch import Config, fetch_relevant, select_relevant

res = fetch_relevant(url, "question")  # fetch, then select
res = select_relevant(html_or_text, "question")  # a document you already have
print(res.status, res.text, res.jev_input_tokens)
```

The async versions are `fetch_relevant_async` and `select_relevant_async`. Use `Config` to set the thresholds, window size, and Jev model. When the URL is a PDF or other file, `res.saved` holds the path where it was saved.

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

Tests need no API key and make no network requests, except that tiktoken downloads its `cl100k_base` encoding the first time it runs on a machine. CI runs them on pushes to main and on pull requests.

`tests/test_end_to_end.py` runs a test page through the whole pipeline and replays recorded Jev responses. Changing extraction, prompts, or thresholds can change the requests, and the test then fails until you re-record the responses with a key:

```bash
JEVFETCH_RECORD=1 uv run pytest tests/test_end_to_end.py
```

`bench/` holds a regression benchmark (`uv run python -m bench`): 10 real page snapshots, 31 questions (27 with verbatim answers, 4 that the page doesn't answer), recorded Jev responses, and a baseline that CI compares against. There are also two manual comparisons with Claude Code's WebFetch, which cost money to run. One compares the two tools directly, and the other has Claude Code answer questions using each one. See [bench/README.md](bench/README.md).

## Disclosure

jevfetch is not affiliated with TypeSafe. a2sys received no funding, credits, or early access from TypeSafe.

## License

[MIT](LICENSE)

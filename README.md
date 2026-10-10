# jevfetch

[![ci](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml/badge.svg)](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

[한국어](README.ko.md)

**Give an LLM agent the parts of a web page that answer its question, quoted verbatim.**

Use it in place of Claude Code's WebFetch. Measured on 32 documentation questions with the page URL given, two runs each in Korean and in English:

| compared with WebFetch | agent time | cost |
|---|---|---|
| on Haiku 4.5 | 30 to 32% less | 42 to 43% less |
| on Haiku 5.5 | 42 to 47% less | 3 to 13% less |

Rubric fact checks matched: 124 of 126 against WebFetch's 126. The cost difference on English questions against Haiku 5.5 is within the uncertainty interval. Conditions, tables and limits: [bench/RESULTS.md](bench/RESULTS.md).

Agents usually read web pages in one of two ways. Tools such as WebFetch use a small model to answer from the page, so the agent gets a paraphrase without the source text. Passing the whole page instead uses more context and costs more. jevfetch splits the page into blocks, asks TypeSafe's judgment model [Jev](https://docs.typesafe.ai) whether each block answers the question, and returns the matching blocks exactly as they appear on the page.


## Quick start

These steps set up Claude Code. You need [uv](https://docs.astral.sh/uv/), Node.js (for `npx`), and a [TypeSafe](https://typesafe.ai) API key.

1. Add your API key to your shell profile (`~/.bashrc` for bash), then open a new terminal and start Claude Code from it:

   ```bash
   echo 'export TYPESAFE_API_KEY=<your key>' >> ~/.zshrc
   ```

2. Install the [jevfetch skill](skills/jevfetch/SKILL.md) in your project. Without it, Claude Code keeps using WebFetch. The skill tells it to read pages with jevfetch, including pages found with WebSearch, and how to handle each status:

   ```bash
   npx skills add a2sys-ai/jevfetch --skill jevfetch -a claude-code
   ```

3. Allow jevfetch to run without a permission prompt. Add this to `.claude/settings.json` in your project, or add the entry to `permissions.allow` if the file already exists:

   ```json
   {
     "permissions": {
       "allow": ["Bash(jevfetch:*)"]
     }
   }
   ```

Open Claude Code in the project and ask something that needs a documentation page. The first time, Claude Code installs the `jevfetch` command if it is missing, and asks for permission first unless your settings already allow it. For other agents, installing without Node.js, or turning WebFetch off, see [More agent setup](#more-agent-setup).

## Command-line use

The skill installs jevfetch when it needs it. To install it yourself (Python 3.12+ is required):

```bash
uv tool install git+https://github.com/a2sys-ai/jevfetch
```

Chrome or Chromium is optional and is used for pages that load their content with JavaScript. Run it with a URL and a question:

```bash
jevfetch https://docs.python.org/3/library/functools.html "What happens if lru_cache maxsize is None?"
```

Output (trimmed):

```text
# jevfetch: https://docs.python.org/3/library/functools.html
# status: filtered (blocks are quoted from the page; '##' lines are the page's heading path)
# 8/133 blocks, 403 of 6009 tokens
## functools — Higher-order functions and operations on callable objects
Source code: Lib/functools.py
## functools — Higher-order functions and operations on callable objects > @functools.lru_cache(maxsize=128, typed=False)
Decorator to wrap a function with a memoizing callable that saves up to the maxsize most recent calls. ...
If maxsize is set to None, the LRU feature is disabled and the cache can grow without bound.
...
```

The agent gets 403 of the page's 6,009 tokens. Each `##` line is the heading path of the passage below it. Definition-list terms such as function signatures are included in the path, so the agent can tell that the sentence about `maxsize=None` belongs to `lru_cache`. The text is copied from the page. jevfetch only collapses whitespace, separates table cells with ` | `, adds `- ` before merged list items, and adds the `##` lines. This call used 38,624 Jev input tokens (about $0.0016) with an empty cache.

| Status | Meaning | Exit code |
|---|---|---|
| `filtered` | Blocks above the threshold, plus the first block. If the blocks other than the first add up to less than 300 tokens, the next highest-scoring blocks are added | 0 |
| `passthrough` | The page is 2,000 tokens or less, so it is returned whole | 0 |
| `no_match` | No block passed the threshold, so the highest-scoring blocks are returned. The answer may still be on the page | 0 |
| `empty` | No text could be extracted | 0 |
| `fetch_error` | The page could not be fetched, or the URL is a PDF or other non-HTML file. For a non-HTML file, the error shows the content type and a `# saved:` line gives the path of the downloaded file | 1 |

If a Jev request fails (missing key, no credits), jevfetch exits with code 2. Options: `--json` prints the result as JSON with token counts and Jev usage, `--no-render` disables the headless browser fallback, and `--model` sets the Jev model.

jevfetch takes a URL. For HTML, Markdown, or plain text you already have, use the [Python API](#python-api). jevfetch does not pick passages from PDFs and other binary files. Like WebFetch, it saves them and prints the path, so the agent can open them with its file reader.

## More agent setup

The [skills](https://github.com/vercel-labs/skills) installer works with Claude Code, Codex, and many other coding agents. By default it installs into the current project. Use `-g` to install for your user, and `-a <agent>` to choose the agents. It needs Node.js. Without Node.js, install the skill for Claude Code manually (use `.claude/skills/` in the project instead of `~/.claude/skills/` to install it for one project):

```bash
mkdir -p ~/.claude/skills/jevfetch
curl -fsSL https://raw.githubusercontent.com/a2sys-ai/jevfetch/main/skills/jevfetch/SKILL.md -o ~/.claude/skills/jevfetch/SKILL.md
```

To make Claude Code read every page with jevfetch, you can turn WebFetch off. Add a deny rule to `.claude/settings.json` in the project, or to `.claude/settings.local.json` to apply it only to yourself. For a single session, start Claude Code with `--disallowedTools WebFetch`.

```json
{
  "permissions": {
    "deny": ["WebFetch"]
  }
}
```

PDFs and other files still reach the agent: jevfetch saves them, and the agent opens the saved file with Read. Keep WebFetch on in projects that summarize whole pages, since jevfetch does not.

For agents that do not support skills, add these lines to the agent's instruction file (`AGENTS.md`, `CLAUDE.md`, and so on):

```
To get a specific fact from a web page, including pages found by web search, run `jevfetch <url> "<question>"` instead of fetching the whole page.
Its output is quoted from the page, so there is no need to fetch the page again to check it.
If the status is no_match, ask a more specific question or try another page. For a PDF or another file, jevfetch prints a `# saved:` line; open that file with your file reader.
```

## When to use it

jevfetch is built for looking up specific facts on long pages: documentation, references, Wikipedia.

Use something else when:
- The task needs the whole page, such as a summary or translation. jevfetch returns only parts of the page.
- The pages are short. Pages of 2,000 tokens or less are returned whole, so jevfetch adds nothing.
- The URL is a PDF or other file. jevfetch picks passages only from HTML and plain text, and returns `fetch_error` with the content type for anything else, without calling Jev. It saves the file so the agent can open it with Read.

## Privacy and security

- jevfetch sends the page text and your question to the TypeSafe API.
- Jev responses are cached in `~/.cache/jevfetch` (change it with `JEVFETCH_CACHE_DIR`). The cache is safe to delete.
- PDFs and other non-HTML files are saved in a `jevfetch-<uid>` folder in the system's temporary directory (change it with `JEVFETCH_FILES_DIR`).
- jevfetch follows redirects and fetches any URL it is given. If you run it as a service, restrict which URLs it can fetch.

## How it works

1. Fetch the page. If the static HTML has less than 200 tokens of text, render it in headless Chrome.
2. Split the page into blocks, each tagged with its heading path, and drop navigation, footers, and other page chrome. A sentence ending in a colon is merged with the list items that follow it under the same heading, up to 1,500 characters, so that a condition it states stays with the items.
3. Return documents of 2,000 tokens or less as they are.
4. Stage 1: group blocks into windows of about 3,000 tokens and send one Jev request per window, with a yes/no question for each block. Blocks scoring 0.3 or higher become candidates.
5. Stage 2: ask about each candidate again on its own, with up to 400 characters of the neighboring blocks as context. Keep blocks scoring 0.8 or higher.
6. Always keep the first block, since its heading path usually contains the page title. If the other kept blocks add up to less than 300 tokens, add the highest-scoring remaining blocks.

Requests within each stage run concurrently.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `TYPESAFE_API_KEY` | none | Jev API key. Not needed if every request is served from the cache |
| `JEVFETCH_CACHE_DIR` | `~/.cache/jevfetch` | Jev response cache directory |
| `JEVFETCH_FILES_DIR` | `jevfetch-<uid>` in the system's temporary directory | Directory for saved PDFs and other non-HTML files |
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

Async versions: `fetch_relevant_async` and `select_relevant_async`. Use `Config` to set the thresholds, window size, and Jev model. When the URL is a PDF or other file, `res.saved` is the path where it was saved.

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

Tests need no API key and make no network requests, except that tiktoken downloads its `cl100k_base` encoding the first time it runs on a machine. CI runs them on pushes to main and on pull requests. `tests/test_end_to_end.py` runs a test page through the whole pipeline and replays recorded Jev responses. Changing extraction, prompts, or thresholds can change the requests, and the test then fails until you re-record the responses with a key:

```bash
JEVFETCH_RECORD=1 uv run pytest tests/test_end_to_end.py
```

`bench/` holds a regression benchmark: 10 real page snapshots, 31 questions (27 with verbatim answers, 4 that the page does not answer), recorded Jev responses, and a baseline that CI compares against (`uv run python -m bench`). It also has two manual, paid comparisons with Claude Code's WebFetch: the tool alone, and Claude Code answering questions with either reader. See [bench/README.md](bench/README.md).

## Disclosure

jevfetch is not affiliated with TypeSafe. a2sys received no funding, credits, or early access from TypeSafe.

## License

[MIT](LICENSE)

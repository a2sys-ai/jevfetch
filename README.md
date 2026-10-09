# jevfetch

[![ci](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml/badge.svg)](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

[한국어](README.ko.md)

**Give an LLM agent the parts of a web page that answer its question, quoted verbatim.**

Agents usually read web pages in one of two ways. Tools such as WebFetch use a small model to answer from the page, so the agent gets a paraphrase without the source text. Passing the whole page instead uses more context and costs more. jevfetch splits the page into blocks, asks TypeSafe's judgment model [Jev](https://docs.typesafe.ai) whether each block answers the question, and returns the matching blocks exactly as they appear on the page.

On a 32-question web-documentation suite asked in Korean and in English with the page URL given, jevfetch's mean agent-run duration was 42–47% shorter than WebFetch with Haiku 5.5 and 30–32% shorter than WebFetch with Haiku 4.5. Observed mean cost was 3–13% lower than with Haiku 5.5 (the English 95% interval includes both a saving and an increase) and 42–43% lower than with Haiku 4.5. jevfetch matched 124 of 126 rubric fact checks per language, against 126 for Haiku 5.5 and 124 Korean, 126 English for Haiku 4.5 (63 rubric items over two repetitions; Claude Code 2.1.295, Sonnet 5.5, the three arms interleaved in random order and run one at a time, 2026-10-09; [how it was measured](bench/README.md)).

Measured with Claude Code (2.1.295, Sonnet 5.5) answering 32 documentation questions, each asked once in Korean and once in English, given the page URL and no web search, reading with WebFetch on Haiku 5.5 (the reader model Claude Code used in these runs), WebFetch on Haiku 4.5 (the reader before it, set with `ANTHROPIC_SMALL_FAST_MODEL`) or jevfetch, two runs per question, the three arms interleaved in random order and run one at a time (2026-10-09; reports: [Korean](bench/reports/agents-2026-10-09-3arm-ko/report.md), [English](bench/reports/agents-2026-10-09-3arm-en/report.md)):

| question language | reader | rubric fact checks matched (of 126) | mean cost per question | of which main model | of which reader model or Jev | main-model input / output tokens | mean turns | `curl` calls (runs) | median time | mean time |
|---|---|---|---|---|---|---|---|---|---|---|
| Korean | WebFetch, Haiku 5.5 | 126 | $0.038 | $0.033 | $0.005 | 16,987 / 1,427 | 2.48 | 19 (9 of 64) | 24.5 s | 24.4 s |
| Korean | WebFetch, Haiku 4.5 | 124 | $0.057 | $0.030 | $0.027 | 17,434 / 1,254 | 2.59 | 29 (13 of 64) | 16.9 s | 19.1 s |
| Korean | jevfetch | 124 | $0.033 | $0.027 | $0.006 | 13,512 / 1,110 | 2.03 | 0 | 12.6 s | 13.0 s |
| English | WebFetch, Haiku 5.5 | 126 | $0.030 | $0.026 | $0.004 | 16,711 / 918 | 2.56 | 28 (12 of 64) | 16.1 s | 18.4 s |
| English | WebFetch, Haiku 4.5 | 126 | $0.050 | $0.026 | $0.024 | 19,484 / 873 | 2.94 | 56 (20 of 64) | 13.6 s | 15.3 s |
| English | jevfetch | 124 | $0.029 | $0.023 | $0.006 | 13,533 / 709 | 2.05 | 0 | 10.4 s | 10.8 s |

Paired over questions (95% bootstrap intervals that resample questions), jevfetch against WebFetch with Haiku 5.5: cost 0.87 (0.78 to 0.98) in Korean and 0.97 (0.85 to 1.13) in English; mean time 0.53 (0.48 to 0.59) and 0.58 (0.53 to 0.65). Against WebFetch with Haiku 4.5: cost 0.57 (0.49 to 0.67) and 0.58 (0.50 to 0.69); mean time 0.68 (0.61 to 0.75) and 0.70 (0.63 to 0.79). The two WebFetch rows differ only in the reader model: Haiku 4.5 costs about seven times more per token, so "of which main model" is about the same while the total differs, and it answers each call faster than Haiku 5.5, which wrote four to five times as many output tokens per run. jevfetch's two misses per language are one sentence on the Redis EXPIRE page that its selection left out every time; the Haiku 4.5 summaries missed two facts in Korean. Cost includes Jev for jevfetch and every Haiku call for WebFetch. `curl` calls count the commands the agent attempted, including refused ones.

By page size (extracted tokens), cost and median time as WebFetch with Haiku 4.5 / WebFetch with Haiku 5.5 / jevfetch:

| pages | questions | Korean: cost | Korean: median time | English: cost | English: median time |
|---|---|---|---|---|---|
| small, under 5,000 | 7 | $0.033 / $0.029 / $0.026 | 13.7 s / 16.9 s / 11.2 s | $0.031 / $0.024 / $0.023 | 12.6 s / 14.4 s / 9.3 s |
| medium, under 20,000 | 16 | $0.060 / $0.040 / $0.031 | 17.2 s / 24.7 s / 13.0 s | $0.054 / $0.032 / $0.027 | 14.1 s / 19.7 s / 10.9 s |
| large, 33,000 to 101,000 | 9 | $0.072 / $0.040 / $0.041 | 17.8 s / 26.3 s / 12.7 s | $0.057 / $0.030 / $0.037 | 14.2 s / 16.1 s / 10.4 s |

Fact checks matched by size, WebFetch 4.5 / 5.5 / jevfetch: small 31/32 / 32/32 / 32/32 in Korean and 32/32 for all in English; medium 75/76 / 76/76 / 74/76 in Korean and 76/76 / 76/76 / 74/76 in English; large 18/18 for all.

Paired cost ratios jevfetch / WebFetch with Haiku 5.5: small 0.89 (0.85 to 0.94) Korean and 0.95 (0.79 to 1.19) English; medium 0.77 (0.69 to 0.88) and 0.84 (0.77 to 0.94); large 1.03 (0.80 to 1.29) and 1.23 (0.86 to 1.67). Mean-time ratios are between 0.51 and 0.64 against Haiku 5.5 and between 0.62 and 0.83 against Haiku 4.5 in every cell. On the large pages (nine questions on three pages) jevfetch's mean cost was above Haiku 5.5 WebFetch's, with intervals that include 1: Jev's cost scales with page length (about $0.023 per call on the 101,000-token RFC 9110), while WebFetch's model pass stays cheap even when the agent calls it again with an offset (1.2 to 1.5 calls and 3.4 turns per run there). Duration was still shorter, and all three found every fact there. Two of the 23 pages (redis.io, docs.stripe.com) serve Markdown when asked for it, and WebFetch then hands the agent the whole page unprocessed instead of a model's answer.

When the agent has to find the page by web search first ([report](bench/reports/agents-2026-10-09/report.md), the 20 Korean questions from the technical report, no URL, WebFetch with Haiku 5.5, runs two at a time), cost per question is the same for both ($0.056, ratio 1.00, interval 0.89 to 1.12), median time is 26.2 s against 20.1 s, and the WebFetch agent went back for the raw page with `curl` in 9 of 40 runs against 1 of 40; with the one-sentence WebFetch instruction of the earlier technical report, WebFetch averaged $0.065 ([ablation](bench/reports/agents-2026-10-09-ablation/report.md)). At the tool level on 27 English questions, three runs each, jevfetch returned the reference sentences verbatim in 81 of 81 outputs against 25 of 81 for a single WebFetch call ([tool comparison](bench/reports/webfetch-2026-10-09.md)).

What these numbers are, and are not:

- A pilot on a small corpus: 32 questions on 23 pages. Intervals resample questions only, so they do not cover run-to-run or API-condition variation.
- Rubric scores measure whether required content is present, not whether the whole answer is correct. 126 is 63 rubric items checked over two repetitions.
- Both agents received instructions of the same shape, so the comparison is between each reader as configured, instructions included.
- Time is the duration Claude Code reports for the whole agent task, not the tool call alone; it leaves out process start and exit. By subprocess wall clock the time ratios are 0.56 and 0.62 against Haiku 5.5 and 0.70 and 0.73 against Haiku 4.5.
- Bash allow rules named `curl`, `grep` and `head`. Per arm and language, 2 to 5 WebFetch runs had a command refused and 2 to 9 had a `grep` pattern rejected by the machine's `grep` (ugrep); no jevfetch run had either. Those turns stay in the measured runs.
- Costs are as billed, prompt caching included. The page bytes fetched and the Jev request bodies were not archived, so a run's reader inputs cannot be replayed exactly.
- After grading, one rubric notation and one proximity window were corrected and every set re-scored; the window change moved a single WebFetch run from 125 to 126. The concurrency and seed fields were written into the run metadata afterwards from the launch command.

How it is measured: [bench/README.md](bench/README.md).

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

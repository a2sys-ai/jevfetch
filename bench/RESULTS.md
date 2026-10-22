# Measured against WebFetch

On a 30-question web-documentation suite asked in Korean and in English with the page URL given, jevfetch's mean agent-run duration was 43–49% shorter than WebFetch with Haiku 5.5 and 32–34% shorter than WebFetch with Haiku 4.5. Observed mean cost was 11% lower than with Haiku 5.5 in Korean and 1% higher in English (both 95% intervals include no difference) and 43–44% lower than with Haiku 4.5. jevfetch and WebFetch with Haiku 5.5 each matched all 116 rubric fact checks per language, and WebFetch with Haiku 4.5 matched 114 in Korean and 116 in English (58 rubric items over two repetitions; Claude Code 2.1.295, Sonnet 5.5, the three arms interleaved in random order and run one at a time, 2026-10-09). The 30 are the questions on which WebFetch answered through its reader model; the two left out are described below.

The agent had no web search. Haiku 5.5 is the reader model Claude Code used in these runs; Haiku 4.5, the reader before it, was set with `ANTHROPIC_SMALL_FAST_MODEL`. The reports ([Korean](reports/agents-2026-10-09-3arm-ko/report.md), [English](reports/agents-2026-10-09-3arm-en/report.md)) cover 32 questions, and two are left out of the figures below. Their pages (redis.io, docs.stripe.com) serve Markdown when asked for it, and in every WebFetch run of both questions WebFetch handed the agent the whole page with no reader-model call, so they do not measure WebFetch's answers. On them every WebFetch run matched all facts; jevfetch matched all on Stripe and 3 of 4 on Redis EXPIRE in every run, its selection leaving out one sentence. The figures below are the remaining 30 questions on 21 pages:

| question language | reader | rubric fact checks matched (of 116) | mean cost per question | of which main model | of which reader model or Jev | main-model input / output tokens | mean turns | `curl` calls (runs) | median time | mean time |
|---|---|---|---|---|---|---|---|---|---|---|
| Korean | WebFetch, Haiku 5.5 | 116 | $0.036 | $0.031 | $0.005 | 16,743 / 1,417 | 2.52 | 19 (9 of 60) | 24.8 s | 25.1 s |
| Korean | WebFetch, Haiku 4.5 | 114 | $0.057 | $0.028 | $0.029 | 17,218 / 1,230 | 2.63 | 29 (13 of 60) | 17.2 s | 19.5 s |
| Korean | jevfetch | 116 | $0.032 | $0.026 | $0.006 | 13,316 / 1,097 | 2.03 | 0 | 12.4 s | 12.8 s |
| English | WebFetch, Haiku 5.5 | 116 | $0.028 | $0.024 | $0.004 | 16,459 / 922 | 2.60 | 28 (12 of 60) | 16.9 s | 19.0 s |
| English | WebFetch, Haiku 4.5 | 116 | $0.049 | $0.024 | $0.025 | 19,415 / 875 | 3.00 | 56 (20 of 60) | 13.9 s | 15.7 s |
| English | jevfetch | 116 | $0.028 | $0.022 | $0.006 | 13,306 / 714 | 2.05 | 0 | 10.4 s | 10.8 s |

Paired over questions (95% bootstrap intervals that resample questions), jevfetch against WebFetch with Haiku 5.5: cost 0.89 (0.79 to 1.004) in Korean and 1.01 (0.86 to 1.18) in English; mean time 0.51 (0.47 to 0.56) and 0.57 (0.51 to 0.63). Against WebFetch with Haiku 4.5: cost 0.56 (0.48 to 0.66) and 0.57 (0.49 to 0.68); mean time 0.66 (0.59 to 0.73) and 0.68 (0.61 to 0.76). The two WebFetch rows differ only in the reader model: Haiku 4.5 costs about seven times more per token, so "of which main model" is about the same while the total differs, and it answers each call faster than Haiku 5.5, which wrote four to five times as many output tokens per run. The Haiku 4.5 summaries missed two facts in Korean. Cost and time cover each run up to its final answer, including the turns in which a WebFetch agent went back to the page with `curl`. Cost includes Jev for jevfetch and every Haiku call for WebFetch. `curl` calls count the commands the agent attempted, including refused ones.

By page size (extracted tokens), cost and median time as WebFetch with Haiku 4.5 / WebFetch with Haiku 5.5 / jevfetch:

| pages | questions | Korean: cost | Korean: median time | English: cost | English: median time |
|---|---|---|---|---|---|
| small, under 5,000 | 6 | $0.031 / $0.027 / $0.024 | 14.3 s / 17.9 s / 11.0 s | $0.030 / $0.023 / $0.022 | 12.8 s / 15.4 s / 9.2 s |
| medium, under 20,000 | 15 | $0.059 / $0.037 / $0.030 | 17.9 s / 25.4 s / 12.7 s | $0.053 / $0.029 / $0.025 | 14.6 s / 20.2 s / 10.9 s |
| large, 33,000 to 101,000 | 9 | $0.072 / $0.040 / $0.041 | 17.8 s / 26.3 s / 12.7 s | $0.057 / $0.030 / $0.037 | 14.2 s / 16.1 s / 10.4 s |

Fact checks matched by size, WebFetch 4.5 / 5.5 / jevfetch: small 29/30 / 30/30 / 30/30 in Korean and 30/30 for all in English; medium 67/68 / 68/68 / 68/68 in Korean and 68/68 for all in English; large 18/18 for all.

Paired cost ratios jevfetch / WebFetch with Haiku 5.5: small 0.89 (0.85 to 0.95) Korean and 0.98 (0.77 to 1.27) English; medium 0.80 (0.71 to 0.90) and 0.88 (0.80 to 0.96); large 1.03 (0.80 to 1.29) and 1.23 (0.86 to 1.67). Mean-time ratios are between 0.49 and 0.64 against Haiku 5.5 and between 0.61 and 0.78 against Haiku 4.5 in every cell. On the large pages (nine questions on three pages) jevfetch's mean cost was above Haiku 5.5 WebFetch's, with intervals that include 1: Jev's cost scales with page length (about $0.023 per call on the 101,000-token RFC 9110), while WebFetch's model pass stays cheap even when the agent calls it again with an offset (1.2 to 1.5 calls and 3.4 turns per run there). Duration was still shorter, and all three found every fact there.

When the agent has to find the page by web search first ([report](reports/agents-2026-10-09/report.md), the 20 Korean questions, Redis EXPIRE and Stripe included, no URL, WebFetch with Haiku 5.5, runs two at a time), cost per question is the same for both ($0.056, ratio 1.00, interval 0.89 to 1.12), median time is 26.2 s against 20.1 s, and the WebFetch agent went back for the raw page with `curl` in 9 of 40 runs against 1 of 40; with a one-sentence WebFetch instruction in place of the instruction file, WebFetch averaged $0.065 ([ablation](reports/agents-2026-10-09-ablation/report.md)). At the tool level on 27 English questions, three runs each, jevfetch returned the reference sentences verbatim in 81 of 81 outputs against 25 of 81 for a single WebFetch call ([tool comparison](reports/webfetch-2026-10-09.md)).

What these numbers are, and are not:

- A pilot on a small corpus: 30 questions on 21 pages. Intervals resample questions only, so they do not cover run-to-run or API-condition variation.
- Rubric scores measure whether required content is present, not whether the whole answer is correct. 116 is 58 rubric items checked over two repetitions.
- Both agents received instructions of the same shape, so the comparison is between each reader as configured, instructions included.
- Time is the duration Claude Code reports for the whole agent task, not the tool call alone; it leaves out process start and exit. By subprocess wall clock the time ratios are 0.54 and 0.60 against Haiku 5.5 and 0.68 and 0.71 against Haiku 4.5.
- Bash allow rules named `curl`, `grep` and `head`. Per arm and language, 2 to 5 WebFetch runs had a command refused and 2 to 9 had a `grep` pattern rejected by the machine's `grep` (ugrep); no jevfetch run had either. Those turns stay in the measured runs.
- Costs are as billed, prompt caching included. The page bytes fetched and the Jev request bodies were not archived, so a run's reader inputs cannot be replayed exactly.
- After grading, one rubric notation and one proximity window were corrected and every set re-scored; the window change added one fact to a single WebFetch run.

How it is measured: [bench/README.md](README.md).

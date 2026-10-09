# Agent-level comparison, 2026-10-09

- Claude Code `claude --version`: 2.1.295 (Claude Code); versions seen in traces: 2.1.295; orchestrator model: sonnet; models billed: claude-haiku-5-5, claude-sonnet-5-5; Jev models: n/a
- jevfetch revision 8d38867; instruction sha1 recorded at run time: webfetch ['f78365cad4']; allowed tools: webfetch ['WebSearch WebFetch Bash(curl:*) Bash(grep:*) Bash(head:*)']
- mode: no URL, WebSearch; question language: ko; small model override: None
- questions: 20; runs per arm: webfetch 40; schedule seed None; bootstrap seed 0; arm order randomized within each (question, repetition) block, block order random
- failures: webfetch: 0 unfinished, 0 timed out, 0 hit the turn limit, 0 retried API errors ($0.0000 spent on failed attempts, not in the means), 8 runs with a Bash command refused (allow rules or variable check)
- all finished runs graded
- Cost: `total_cost_usd` of the `claude -p` run (main model plus WebFetch's reader model) plus, for jevfetch, the Jev input tokens actually sent during the run (one recording per request in the run's own cache) at $0.042/Mtok. Time: the run's `duration_ms`. Unfinished runs count as zero facts and are excluded from cost and time means. 'Of which Haiku' is every non-orchestrator model billed in the run: WebFetch's reader and Claude Code's own background calls, which occur in both arms.

## Summary

| arm | rubric facts matched / checked | runs finished | mean cost per question (USD) | of which main model | of which Haiku | of which Jev | median seconds | mean seconds | mean turns | main-agent input tokens | main-agent output tokens | reader calls per run | curl calls (runs) | runs with a refused command |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| webfetch | 101/102 | 40/40 | 0.0645 | 0.0516 | 0.0129 | 0.0000 | 27.7 | 35.1 | 4.38 | 25580 | 2343 | 2.55 | 18 (9) | 8 |

## Paired comparison (jevfetch relative to each WebFetch arm, 95% bootstrap interval clustered by question)

- none (needs the jevfetch arm and at least one WebFetch arm)

## By page size (extracted tokens: small < 5,000, medium < 20,000, large) and language

| bucket | lang | questions | arm | facts | mean cost | main model | Haiku | Jev | median s | mean turns | main input tok | main output tok | reader calls/run | curl calls (runs) | cost ratio (interval) | mean-time ratio (interval) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| medium | ko | 13 | webfetch | 69/70 | 0.0751 | 0.0587 | 0.0165 | 0.0000 | 34.7 | 4.77 | 28636 | 2613 | 2.73 | 14 (7) |  |  |
| small | ko | 7 | webfetch | 32/32 | 0.0447 | 0.0386 | 0.0061 | 0.0000 | 22.1 | 3.64 | 19905 | 1843 | 2.21 | 4 (2) |  |  |

## Judge votes that were not unanimous (0 of 26 judged runs; review by hand before publishing)

- none

## Per run

| question | size | lang | arm | rep | finished | facts | cost | Jev | seconds | turns | main input tok | jevfetch calls | WebFetch calls | curl calls | denied | answer sha1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-cache | medium | ko | webfetch | 0 | yes | 4/4 | 0.0497 | 0.0000 | 32.5 | 3 | 20028 | 0 | 2 | 0 | 0 | 056287327107 |
| claude-cache | medium | ko | webfetch | 1 | yes | 4/4 | 0.0541 | 0.0000 | 35.9 | 3 | 20410 | 0 | 2 | 0 | 0 | 3a1ea015b57e |
| docker-swap | small | ko | webfetch | 0 | yes | 2/2 | 0.0235 | 0.0000 | 17.6 | 2 | 11712 | 0 | 1 | 0 | 0 | 80be31f586b4 |
| docker-swap | small | ko | webfetch | 1 | yes | 2/2 | 0.0269 | 0.0000 | 22.1 | 2 | 11982 | 0 | 1 | 0 | 0 | 08c955c2c076 |
| gcs-lifecycle | small | ko | webfetch | 0 | yes | 3/3 | 0.0515 | 0.0000 | 33.8 | 5 | 20440 | 0 | 4 | 0 | 0 | b6ee6ec933a8 |
| gcs-lifecycle | small | ko | webfetch | 1 | yes | 3/3 | 0.0342 | 0.0000 | 24.8 | 3 | 18583 | 0 | 2 | 0 | 0 | 873b1907a936 |
| gdpr-fines | medium | ko | webfetch | 0 | yes | 2/2 | 0.0697 | 0.0000 | 45.0 | 5 | 29643 | 0 | 3 | 0 | 0 | 4d1dd994413c |
| gdpr-fines | medium | ko | webfetch | 1 | yes | 2/2 | 0.0941 | 0.0000 | 56.8 | 6 | 41240 | 0 | 3 | 0 | 1 | 3d0a4bc95a8a |
| gh-limits | small | ko | webfetch | 0 | yes | 3/3 | 0.0397 | 0.0000 | 22.1 | 4 | 19306 | 0 | 3 | 0 | 0 | 07e7c0adb53a |
| gh-limits | small | ko | webfetch | 1 | yes | 3/3 | 0.0394 | 0.0000 | 21.3 | 4 | 19269 | 0 | 3 | 0 | 0 | 9f18528ce158 |
| gh-rest-rate | small | ko | webfetch | 0 | yes | 3/3 | 0.0267 | 0.0000 | 18.9 | 2 | 12104 | 0 | 1 | 0 | 0 | a1b855fd2bb6 |
| gh-rest-rate | small | ko | webfetch | 1 | yes | 3/3 | 0.0241 | 0.0000 | 17.8 | 2 | 12074 | 0 | 1 | 0 | 0 | efe62bc342ec |
| git-lease | medium | ko | webfetch | 0 | yes | 2/2 | 0.0403 | 0.0000 | 28.4 | 2 | 12937 | 0 | 1 | 0 | 0 | 5e7e27e3e26c |
| git-lease | medium | ko | webfetch | 1 | yes | 2/2 | 0.0372 | 0.0000 | 27.1 | 2 | 12661 | 0 | 1 | 0 | 0 | 6a36ed10a7af |
| k8s-termination | medium | ko | webfetch | 0 | yes | 3/3 | 0.0631 | 0.0000 | 36.4 | 4 | 22790 | 0 | 3 | 0 | 0 | 077eaf669e68 |
| k8s-termination | medium | ko | webfetch | 1 | yes | 3/3 | 0.0994 | 0.0000 | 48.5 | 7 | 36721 | 0 | 5 | 2 | 1 | b421127ed48f |
| ko-holiday | medium | ko | webfetch | 0 | yes | 1/1 | 0.1559 | 0.0000 | 99.2 | 11 | 69304 | 0 | 7 | 1 | 0 | 618191252ef7 |
| ko-holiday | medium | ko | webfetch | 1 | yes | 1/1 | 0.1774 | 0.0000 | 106.9 | 10 | 77097 | 0 | 5 | 2 | 0 | fef2008c1125 |
| ko-minwage | medium | ko | webfetch | 0 | yes | 3/4 | 0.1144 | 0.0000 | 60.5 | 9 | 38946 | 0 | 4 | 3 | 0 | 5503187e7212 |
| ko-minwage | medium | ko | webfetch | 1 | yes | 4/4 | 0.1291 | 0.0000 | 63.3 | 8 | 63415 | 0 | 3 | 2 | 1 | 7cdcd0063ea0 |
| mdn-keepalive | small | ko | webfetch | 0 | yes | 1/1 | 0.0936 | 0.0000 | 44.3 | 9 | 52754 | 0 | 4 | 3 | 1 | 78a9e834649a |
| mdn-keepalive | small | ko | webfetch | 1 | yes | 1/1 | 0.1017 | 0.0000 | 49.9 | 8 | 43242 | 0 | 5 | 1 | 1 | a9b9b9e2d9a1 |
| nginx-read-timeout | medium | ko | webfetch | 0 | yes | 2/2 | 0.0218 | 0.0000 | 13.8 | 2 | 11734 | 0 | 1 | 0 | 0 | 93d9ed9e8ffd |
| nginx-read-timeout | medium | ko | webfetch | 1 | yes | 2/2 | 0.0226 | 0.0000 | 15.4 | 2 | 11755 | 0 | 1 | 0 | 0 | 1135624704c1 |
| npm-peer | medium | ko | webfetch | 0 | yes | 3/3 | 0.0572 | 0.0000 | 23.8 | 4 | 13961 | 0 | 2 | 0 | 0 | f87852ab16ac |
| npm-peer | medium | ko | webfetch | 1 | yes | 3/3 | 0.0616 | 0.0000 | 24.8 | 4 | 14310 | 0 | 2 | 0 | 0 | b1a6a788d528 |
| pg-wraparound | medium | ko | webfetch | 0 | yes | 2/2 | 0.0706 | 0.0000 | 38.4 | 5 | 25884 | 0 | 4 | 0 | 0 | 00bbddf7e515 |
| pg-wraparound | medium | ko | webfetch | 1 | yes | 2/2 | 0.0776 | 0.0000 | 45.9 | 5 | 26640 | 0 | 4 | 0 | 0 | c2582ff19e39 |
| py-subprocess | medium | ko | webfetch | 0 | yes | 2/2 | 0.0448 | 0.0000 | 29.8 | 3 | 13255 | 0 | 1 | 0 | 1 | c34ab9a5df46 |
| py-subprocess | medium | ko | webfetch | 1 | yes | 2/2 | 0.0687 | 0.0000 | 33.5 | 3 | 14471 | 0 | 1 | 0 | 0 | 43b962b1cff0 |
| redis-expire | medium | ko | webfetch | 0 | yes | 4/4 | 0.0850 | 0.0000 | 18.6 | 2 | 24870 | 0 | 1 | 0 | 0 | e7a161beb651 |
| redis-expire | medium | ko | webfetch | 1 | yes | 4/4 | 0.0818 | 0.0000 | 16.4 | 2 | 24902 | 0 | 1 | 0 | 0 | 75120a9f2ece |
| rfc9111-heuristic | medium | ko | webfetch | 0 | yes | 4/4 | 0.0942 | 0.0000 | 55.0 | 8 | 39631 | 0 | 6 | 2 | 1 | 24ca3be86e6b |
| rfc9111-heuristic | medium | ko | webfetch | 1 | yes | 4/4 | 0.0997 | 0.0000 | 58.8 | 8 | 52085 | 0 | 6 | 2 | 1 | 196afbe37984 |
| sqlite-length | small | ko | webfetch | 0 | yes | 3/3 | 0.0387 | 0.0000 | 23.0 | 3 | 13112 | 0 | 2 | 0 | 0 | 1922d1aab8b2 |
| sqlite-length | small | ko | webfetch | 1 | yes | 3/3 | 0.0371 | 0.0000 | 22.9 | 3 | 12865 | 0 | 2 | 0 | 0 | 84637a3aaff7 |
| stripe-rate | small | ko | webfetch | 0 | yes | 1/1 | 0.0456 | 0.0000 | 17.0 | 2 | 15618 | 0 | 1 | 0 | 0 | 0a9b48286f97 |
| stripe-rate | small | ko | webfetch | 1 | yes | 1/1 | 0.0432 | 0.0000 | 15.5 | 2 | 15607 | 0 | 1 | 0 | 0 | a68d78ee0d39 |
| us-dst | medium | ko | webfetch | 0 | yes | 2/2 | 0.0430 | 0.0000 | 19.9 | 3 | 13014 | 0 | 1 | 0 | 0 | 5800130de568 |
| us-dst | medium | ko | webfetch | 1 | yes | 2/2 | 0.0405 | 0.0000 | 18.9 | 3 | 12822 | 0 | 1 | 0 | 0 | f877c850c0ea |

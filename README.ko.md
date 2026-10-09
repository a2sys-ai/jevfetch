# jevfetch

[![ci](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml/badge.svg)](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

[English](README.md)

**웹 페이지에서 질문에 답이 되는 부분만 골라 원문 그대로 LLM 에이전트에 넘긴다.**

에이전트가 웹 페이지를 읽는 방법은 보통 두 가지다. WebFetch 같은 도구는 작은 모델이 페이지를 읽고 답을 써 주기 때문에, 에이전트는 원문 없이 요약만 받는다. 페이지 전체를 넘기면 컨텍스트를 많이 차지하고 비용도 커진다. jevfetch는 페이지를 블록 단위로 나누고, TypeSafe의 판정 모델 [Jev](https://docs.typesafe.ai)로 블록마다 질문에 답이 되는지 판단해, 답이 되는 블록만 원문 그대로 돌려준다.

페이지 URL을 준 웹 문서 질문 32개를 한국어와 영어로 각각 풀었을 때, jevfetch의 평균 에이전트 실행 시간은 Haiku 5.5를 쓰는 WebFetch보다 42~47%, Haiku 4.5를 쓰는 WebFetch보다 30~32% 짧았다. 관측된 평균 비용은 Haiku 5.5 대비 3~13% 낮았고(영어의 95% 구간은 절감과 증가를 모두 포함) Haiku 4.5 대비 42~43% 낮았다. 루브릭 사실 확인은 언어마다 jevfetch가 126개 중 124개, Haiku 5.5 WebFetch가 126개, Haiku 4.5 WebFetch가 한국어 124개와 영어 126개를 맞혔다(루브릭 항목 63개를 2회 반복, Claude Code 2.1.295, Sonnet 5.5, 세 arm을 무작위 순서로 교차해 한 번에 하나씩 실행, 2026-10-09, [측정 방법](bench/README.md)).

Claude Code(2.1.295, Sonnet 5.5)가 기술 문서 질문 32개를 한국어판과 영어판으로 각각 받되, 페이지 URL을 받고 웹 검색 없이, 읽기 도구만 Haiku 5.5를 쓰는 WebFetch(이 실행에서 Claude Code가 쓴 읽기 모델), Haiku 4.5를 쓰는 WebFetch(그 전 모델, `ANTHROPIC_SMALL_FAST_MODEL`로 지정), jevfetch 셋으로 바꿔 질문당 2회씩 돌린 결과다. 세 arm은 무작위 순서로 교차했고 한 번에 하나씩 실행했다(2026-10-09, 보고서: [한국어](bench/reports/agents-2026-10-09-3arm-ko/report.md), [영어](bench/reports/agents-2026-10-09-3arm-en/report.md)).

| 질문 언어 | 읽기 도구 | 루브릭 사실 확인(126 중) | 질문당 평균 비용 | 그중 메인 모델 | 그중 읽기 모델 또는 Jev | 메인 모델 입력 / 출력 토큰 | 평균 턴 | `curl` 호출(실행 수) | 시간 중앙값 | 시간 평균 |
|---|---|---|---|---|---|---|---|---|---|---|
| 한국어 | WebFetch, Haiku 5.5 | 126 | $0.038 | $0.033 | $0.005 | 16,987 / 1,427 | 2.48 | 19 (64회 중 9) | 24.5초 | 24.4초 |
| 한국어 | WebFetch, Haiku 4.5 | 124 | $0.057 | $0.030 | $0.027 | 17,434 / 1,254 | 2.59 | 29 (64회 중 13) | 16.9초 | 19.1초 |
| 한국어 | jevfetch | 124 | $0.033 | $0.027 | $0.006 | 13,512 / 1,110 | 2.03 | 0 | 12.6초 | 13.0초 |
| 영어 | WebFetch, Haiku 5.5 | 126 | $0.030 | $0.026 | $0.004 | 16,711 / 918 | 2.56 | 28 (64회 중 12) | 16.1초 | 18.4초 |
| 영어 | WebFetch, Haiku 4.5 | 126 | $0.050 | $0.026 | $0.024 | 19,484 / 873 | 2.94 | 56 (64회 중 20) | 13.6초 | 15.3초 |
| 영어 | jevfetch | 124 | $0.029 | $0.023 | $0.006 | 13,533 / 709 | 2.05 | 0 | 10.4초 | 10.8초 |

질문별로 짝지은 비율(질문을 다시 뽑는 95% 부트스트랩 구간)은, Haiku 5.5를 쓰는 WebFetch 대비 jevfetch가 비용 한국어 0.87(0.78~0.98), 영어 0.97(0.85~1.13), 평균 시간 0.53(0.48~0.59), 0.58(0.53~0.65)이다. Haiku 4.5를 쓰는 WebFetch 대비로는 비용 0.57(0.49~0.67), 0.58(0.50~0.69), 평균 시간 0.68(0.61~0.75), 0.70(0.63~0.79)이다. 두 WebFetch 행의 차이는 읽기 모델뿐이다. Haiku 4.5는 토큰당 약 7배 비싸서 "그중 메인 모델"은 비슷하고 총액만 다르며, 실행당 출력 토큰을 4~5배 쓰는 Haiku 5.5보다 호출당 답이 빨리 나온다. jevfetch가 두 언어에서 각각 놓친 2건은 Redis EXPIRE 페이지의 한 문장을 선별이 매번 뺀 것이고, Haiku 4.5 요약은 한국어에서 사실 2개를 빠뜨렸다. 비용에는 jevfetch의 Jev와 WebFetch의 모든 Haiku 호출이 들어 있다. `curl` 호출은 거부된 것을 포함해 에이전트가 시도한 명령 수다.

페이지 크기(추출 토큰)별 비용과 시간 중앙값은 WebFetch(Haiku 4.5) / WebFetch(Haiku 5.5) / jevfetch 순이다.

| 페이지 | 질문 | 한국어: 비용 | 한국어: 시간 중앙값 | 영어: 비용 | 영어: 시간 중앙값 |
|---|---|---|---|---|---|
| 소형, 5,000 미만 | 7 | $0.033 / $0.029 / $0.026 | 13.7초 / 16.9초 / 11.2초 | $0.031 / $0.024 / $0.023 | 12.6초 / 14.4초 / 9.3초 |
| 중형, 20,000 미만 | 16 | $0.060 / $0.040 / $0.031 | 17.2초 / 24.7초 / 13.0초 | $0.054 / $0.032 / $0.027 | 14.1초 / 19.7초 / 10.9초 |
| 대형, 33,000~101,000 | 9 | $0.072 / $0.040 / $0.041 | 17.8초 / 26.3초 / 12.7초 | $0.057 / $0.030 / $0.037 | 14.2초 / 16.1초 / 10.4초 |

크기별 사실 확인(WebFetch 4.5 / 5.5 / jevfetch)은 소형 한국어 31/32 / 32/32 / 32/32, 영어 모두 32/32, 중형 한국어 75/76 / 76/76 / 74/76, 영어 76/76 / 76/76 / 74/76, 대형 모두 18/18이다.

Haiku 5.5 WebFetch 대비 짝지은 비용비는 소형 한국어 0.89(0.85~0.94), 영어 0.95(0.79~1.19), 중형 0.77(0.69~0.88)과 0.84(0.77~0.94), 대형 1.03(0.80~1.29)과 1.23(0.86~1.67)이다. 평균 시간비는 모든 칸에서 Haiku 5.5 대비 0.51~0.64, Haiku 4.5 대비 0.62~0.83이다. 대형 페이지(페이지 3개에 질문 9개)에서는 jevfetch의 평균 비용이 Haiku 5.5 WebFetch보다 높았고 구간은 1을 포함한다. Jev 비용은 페이지 길이에 비례하고(101,000토큰의 RFC 9110은 호출당 약 $0.023) WebFetch는 에이전트가 offset으로 다시 호출해도(실행당 1.2~1.5회 호출, 3.4턴) 모델 비용이 싸기 때문이다. 시간은 그래도 jevfetch가 짧고, 거기서는 셋 모두 사실을 전부 찾았다. 23개 페이지 중 둘(redis.io, docs.stripe.com)은 요청하면 마크다운을 주는데, 그때 WebFetch는 모델의 답 대신 페이지 전체를 그대로 에이전트에 넘긴다.

에이전트가 웹 검색으로 페이지를 먼저 찾아야 하는 조건([보고서](bench/reports/agents-2026-10-09/report.md), 기술 보고서의 한국어 질문 20개, URL 없음, Haiku 5.5 WebFetch, 2개씩 동시 실행)에서는 질문당 비용이 둘 다 $0.056으로 같고(비율 1.00, 구간 0.89~1.12), 시간 중앙값은 26.2초 대 20.1초, WebFetch 에이전트는 40회 중 9회 `curl`로 원문을 다시 받으러 갔고 jevfetch 에이전트는 1회였다. 앞선 기술 보고서의 한 문장짜리 WebFetch 안내로는 WebFetch가 평균 $0.065였다([소거 실험](bench/reports/agents-2026-10-09-ablation/report.md)). 도구 단독 비교(영어 질문 27개, 3회)에서는 jevfetch가 81개 출력 모두에서 기준 문장을 원문 그대로 돌려줬고 WebFetch 1회 호출은 81개 중 25개였다([도구 비교](bench/reports/webfetch-2026-10-09.md)).

이 수치의 성격은 이렇다.

- 작은 코퍼스의 파일럿이다. 페이지 23개에 질문 32개. 구간은 질문만 다시 뽑으므로 실행 간 변동이나 API 상태 변동은 담지 않는다.
- 루브릭 점수는 필요한 내용이 들어 있는지를 재는 것이지 답변 전체의 정확성이 아니다. 126은 루브릭 항목 63개를 2회 반복해 확인한 수다.
- 두 에이전트는 같은 꼴의 안내문을 받았으므로 비교 대상은 안내문을 포함한 각 읽기 도구의 구성이다.
- 시간은 도구 호출만이 아니라 Claude Code가 보고한 에이전트 과제 전체의 소요 시간이며, 프로세스 시작과 종료는 빠져 있다. 서브프로세스 벽시계 기준 시간비는 Haiku 5.5 대비 0.56과 0.62, Haiku 4.5 대비 0.70과 0.73이다.
- Bash 허용 규칙은 `curl`, `grep`, `head`였다. arm·언어마다 WebFetch 실행 2~5회에서 명령이 거부됐고 2~9회에서 이 기계의 `grep`(ugrep)이 패턴을 거절했다. jevfetch 실행에는 둘 다 없었다. 그 턴들은 측정에 그대로 들어 있다.
- 비용은 프롬프트 캐시가 적용된 그대로의 청구액이다. 받아온 페이지 바이트와 Jev 요청 본문은 보관하지 않아 실행의 읽기 입력을 그대로 재현할 수는 없다.
- 채점 뒤에 루브릭 표기 하나와 근접 창 하나를 고쳐 전 세트를 다시 채점했다. 창 수정으로 WebFetch 실행 하나가 125에서 126으로 바뀌었다. 동시성과 시드 필드는 실행 뒤에 실행 명령에서 메타데이터에 적어 넣었다.

측정 방법은 [bench/README.md](bench/README.md)를 참고한다.

## 빠른 시작

Claude Code 기준이다. [uv](https://docs.astral.sh/uv/), Node.js(`npx` 실행용), [TypeSafe](https://typesafe.ai) API 키가 필요하다.

1. API 키를 셸 프로필에 추가하고(bash는 `~/.bashrc`), 새 터미널을 열어 거기서 Claude Code를 실행한다.

   ```bash
   echo 'export TYPESAFE_API_KEY=<API 키>' >> ~/.zshrc
   ```

2. 작업할 프로젝트에 [jevfetch 스킬](skills/jevfetch/SKILL.md)을 설치한다. 스킬이 없으면 Claude Code는 계속 WebFetch를 쓴다. 스킬은 WebSearch로 찾은 페이지를 포함해 웹 페이지를 jevfetch로 읽게 하고, 상태별 처리 방법을 알려 준다.

   ```bash
   npx skills add a2sys-ai/jevfetch --skill jevfetch -a claude-code
   ```

3. 권한 확인 없이 jevfetch를 실행하도록 허용한다. 프로젝트의 `.claude/settings.json`에 아래 내용을 넣는다. 파일이 이미 있으면 `permissions.allow`에 항목만 추가한다.

   ```json
   {
     "permissions": {
       "allow": ["Bash(jevfetch:*)"]
     }
   }
   ```

이제 그 프로젝트에서 Claude Code를 열고 문서를 찾아봐야 하는 질문을 하면 된다. 처음 쓸 때 `jevfetch` 명령이 없으면 Claude Code가 설치하며, 설정에서 허용하지 않았다면 실행 전에 확인을 받는다. 다른 에이전트, Node.js 없이 설치하는 방법, WebFetch 끄기는 [에이전트 추가 설정](#에이전트-추가-설정)을 참고한다.

## 명령으로 직접 쓰기

스킬은 필요할 때 jevfetch를 직접 설치한다. 직접 설치하려면 아래 명령을 실행한다(Python 3.12 이상 필요).

```bash
uv tool install git+https://github.com/a2sys-ai/jevfetch
```

Chrome이나 Chromium은 선택 사항이며, JavaScript로 본문을 불러오는 페이지를 읽을 때 쓴다. URL과 질문을 넘겨 실행한다.

```bash
jevfetch https://docs.python.org/3/library/functools.html "What happens if lru_cache maxsize is None?"
```

출력은 다음과 같다(일부 생략).

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

에이전트는 페이지 6,009토큰 중 403토큰만 받는다. `##` 줄은 바로 아래 발췌가 속한 제목 경로다. 함수 시그니처 같은 정의 목록 항목도 경로에 들어가므로, 에이전트는 `maxsize=None` 설명이 `lru_cache`에 대한 것임을 알 수 있다. 본문은 페이지에서 그대로 가져온다. jevfetch가 하는 일은 연속 공백을 하나로 줄이고, 표 셀 사이에 ` | `를 넣고, 합친 목록 항목 앞에 `- `를 붙이고, `##` 줄을 추가하는 것뿐이다. 캐시가 비어 있을 때 이 호출에 Jev 입력 38,624토큰(약 $0.0016)이 들었다.

| 상태 | 의미 | 종료 코드 |
|---|---|---|
| `filtered` | 임계값을 넘은 블록과 첫 블록. 첫 블록을 뺀 나머지가 300토큰 미만이면 점수가 높은 블록을 더 넣는다 | 0 |
| `passthrough` | 2,000토큰 이하의 짧은 페이지라 전체를 돌려준다 | 0 |
| `no_match` | 임계값을 넘은 블록이 없어 점수가 가장 높은 블록들을 돌려준다. 페이지에 답이 없다는 뜻은 아니다 | 0 |
| `empty` | 본문을 추출하지 못했다 | 0 |
| `fetch_error` | 페이지를 가져오지 못했거나, URL이 PDF 같은 HTML이 아닌 파일이다. HTML이 아닌 파일이면 오류 메시지에 content type이 나오고, `# saved:` 줄에 내려받은 파일의 경로가 나온다 | 1 |

Jev 요청이 실패하면(키 없음, 크레딧 부족) 종료 코드 2로 끝난다. 옵션은 다음과 같다. `--json`은 토큰 수와 Jev 사용량을 포함해 JSON으로 출력하고, `--no-render`는 헤드리스 브라우저 렌더링을 끄고, `--model`은 Jev 모델을 지정한다.

jevfetch는 URL을 받는다. 이미 가진 HTML, 마크다운, 텍스트 문서는 [Python API](#python-api)로 처리한다. PDF 같은 바이너리 파일에서는 구절을 고르지 않는다. 대신 WebFetch처럼 파일을 저장하고 경로를 출력해서, 에이전트가 자기 파일 읽기 도구로 열 수 있게 한다.

## 에이전트 추가 설정

[skills](https://github.com/vercel-labs/skills) 설치 도구는 Claude Code, Codex를 비롯한 여러 코딩 에이전트를 지원한다. 기본적으로 현재 프로젝트에 설치한다. `-g`를 붙이면 현재 사용자의 모든 프로젝트에 설치하고, `-a <에이전트>`로 대상 에이전트를 지정한다. Node.js가 필요하다. Node.js가 없으면 Claude Code용 스킬을 직접 설치한다. 한 프로젝트에만 쓰려면 `~/.claude/skills/` 대신 프로젝트의 `.claude/skills/`에 설치한다.

```bash
mkdir -p ~/.claude/skills/jevfetch
curl -fsSL https://raw.githubusercontent.com/a2sys-ai/jevfetch/main/skills/jevfetch/SKILL.md -o ~/.claude/skills/jevfetch/SKILL.md
```

WebFetch를 끄면 Claude Code가 모든 페이지를 jevfetch로 읽는다. 프로젝트의 `.claude/settings.json`에 deny 규칙을 넣는다. 본인에게만 적용하려면 `.claude/settings.local.json`에 넣고, 한 세션에만 적용하려면 Claude Code를 `--disallowedTools WebFetch`로 실행한다.

```json
{
  "permissions": {
    "deny": ["WebFetch"]
  }
}
```

PDF 같은 파일은 그래도 에이전트에게 전달된다. jevfetch가 파일을 저장하고, 에이전트는 저장된 파일을 Read로 연다. jevfetch는 페이지 전체 요약은 하지 않으므로, 그런 작업이 필요한 프로젝트에서는 WebFetch를 켜 둔다.

스킬을 지원하지 않는 에이전트는 지침 파일(`AGENTS.md`, `CLAUDE.md` 등)에 아래 내용을 넣는다.

```
웹 검색으로 찾은 페이지를 포함해 웹 페이지에서 특정 사실을 찾을 때는 페이지 전체를 받지 말고 `jevfetch <url> "<질문>"`을 쓴다.
출력은 페이지 원문 발췌이므로, 확인하려고 같은 페이지를 다시 받을 필요가 없다.
status가 no_match면 질문을 더 구체적으로 바꾸거나 다른 페이지를 찾는다. PDF 같은 파일이면 jevfetch가 `# saved:` 줄을 출력하니, 그 파일을 파일 읽기 도구로 연다.
```

## 언제 쓰면 좋은가

jevfetch는 기술 문서, 레퍼런스, 위키백과처럼 긴 페이지에서 특정 사실을 찾을 때 쓰도록 만들었다.

다음 경우에는 다른 도구가 낫다.
- 요약이나 번역처럼 페이지 전체가 필요한 작업. jevfetch는 페이지 일부만 돌려준다.
- 짧은 페이지. 2,000토큰 이하는 그대로 돌려주므로 차이가 없다.
- PDF 같은 파일. jevfetch는 HTML과 텍스트에서만 구절을 고르고, 그 밖의 응답은 Jev를 호출하지 않고 content type을 담은 `fetch_error`로 끝낸다. 에이전트가 Read로 열 수 있게 파일은 저장한다.

## 개인정보와 보안

- jevfetch는 페이지 텍스트와 질문을 TypeSafe API로 보낸다.
- Jev 응답은 `~/.cache/jevfetch`에 캐시된다(`JEVFETCH_CACHE_DIR`로 변경). 캐시는 언제 지워도 된다.
- HTML이 아닌 PDF 같은 파일은 시스템 임시 디렉터리의 `jevfetch-<UID>` 폴더에 저장된다(`JEVFETCH_FILES_DIR`로 변경).
- jevfetch는 받은 URL을 리다이렉트까지 따라가서 가져온다. 서비스로 운영한다면 가져올 수 있는 URL을 제한해야 한다.

## 동작 방식

1. 페이지를 가져온다. 정적 HTML의 본문이 200토큰 미만이면 헤드리스 Chrome으로 렌더링한다.
2. 페이지를 블록으로 나누고 블록마다 제목 경로를 붙인다. 내비게이션, 푸터 같은 영역은 버린다. 콜론으로 끝나는 문장은 같은 제목 아래 이어지는 목록 항목과 최대 1,500자까지 한 블록으로 합친다. 문장에 적힌 조건이 목록 항목과 떨어지지 않게 하려는 것이다.
3. 2,000토큰 이하 문서는 그대로 돌려준다.
4. 1단계: 블록을 약 3,000토큰 단위 윈도우로 묶고, 윈도우마다 Jev 요청 하나로 블록별 예/아니오를 묻는다. 점수가 0.3 이상인 블록이 후보가 된다.
5. 2단계: 후보마다 앞뒤 블록을 각각 최대 400자씩 문맥으로 붙여 다시 묻는다. 점수가 0.8 이상인 블록을 남긴다.
6. 첫 블록은 항상 남긴다. 보통 이 블록의 제목 경로에 페이지 제목이 들어 있다. 첫 블록을 뺀 나머지가 300토큰 미만이면 점수가 높은 블록을 더 넣는다.

각 단계 안의 요청은 병렬로 보낸다.

## 설정

| 변수 | 기본값 | 설명 |
|---|---|---|
| `TYPESAFE_API_KEY` | 없음 | Jev API 키. 모든 요청이 캐시에서 처리되면 필요 없다 |
| `JEVFETCH_CACHE_DIR` | `~/.cache/jevfetch` | Jev 응답 캐시 경로 |
| `JEVFETCH_FILES_DIR` | 시스템 임시 디렉터리의 `jevfetch-<UID>` | 저장한 PDF 같은 HTML이 아닌 파일의 경로 |
| `JEVFETCH_CHROME` | 자동 탐색 | 렌더링에 쓸 Chrome 또는 Chromium 실행 파일 |
| `JEVFETCH_USER_AGENT` | jevfetch 이름, 버전, 저장소 주소 | 페이지 요청 시 보내는 User-Agent |

기본 모델은 `jev-latest` 별칭이고 캐시 키에도 이 이름이 들어간다. 그래서 모델이 업데이트된 뒤에도 캐시에서 이전 모델의 답이 나올 수 있다. 결과를 재현하려면 `--model`이나 `Config(model=...)`로 모델 버전을 고정한다.

## Python API

```python
from jevfetch import Config, fetch_relevant, select_relevant

res = fetch_relevant(url, "question")  # fetch, then select
res = select_relevant(html_or_text, "question")  # a document you already have
print(res.status, res.text, res.jev_input_tokens)
```

비동기 버전은 `fetch_relevant_async`, `select_relevant_async`다. 임계값, 윈도우 크기, Jev 모델은 `Config`로 설정한다. URL이 PDF 같은 파일이면 `res.saved`에 저장한 경로가 들어 있다.

## 개발

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

테스트는 API 키가 필요 없고 네트워크 요청도 하지 않는다. 단, tiktoken이 한 기기에서 처음 실행될 때 `cl100k_base` 인코딩을 내려받는다. CI는 main 브랜치 push와 pull request마다 실행한다. `tests/test_end_to_end.py`는 테스트용 페이지를 전체 파이프라인에 통과시키면서 녹화해 둔 Jev 응답을 재생한다. 추출, 프롬프트, 임계값을 바꾸면 요청이 달라질 수 있고, 그러면 키를 넣고 응답을 다시 녹화하기 전까지 이 테스트는 실패한다.

```bash
JEVFETCH_RECORD=1 uv run pytest tests/test_end_to_end.py
```

`bench/`에는 회귀 벤치마크가 있다. 실제 페이지 스냅샷 10개, 질문 31개(원문 정답이 붙은 27개, 페이지에 답이 없는 4개), 기록된 Jev 응답, CI가 비교하는 기준값이다(`uv run python -m bench`). Claude Code의 WebFetch와 비교하는 유료 수동 스크립트가 둘 있다. 도구 단독 비교와, Claude Code가 두 읽기 도구로 질문에 답하는 비교다. [bench/README.md](bench/README.md)를 참고한다.

## 이해관계 고지

jevfetch는 TypeSafe와 관계가 없다. a2sys는 TypeSafe에서 자금, 크레딧, 사전 접근 권한을 받지 않았다.

## 라이선스

[MIT](LICENSE)

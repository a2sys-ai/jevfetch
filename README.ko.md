# jevfetch

[![ci](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml/badge.svg)](https://github.com/a2sys-ai/jevfetch/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

[English](README.md)

**웹 페이지에서 질문에 답이 되는 부분만 골라 원문 그대로 LLM 에이전트에 넘긴다.**

에이전트가 웹 페이지를 읽는 방법은 보통 두 가지다. WebFetch 같은 도구는 작은 모델이 페이지를 읽고 답을 써 주기 때문에, 에이전트는 원문 없이 요약만 받는다. 페이지 전체를 넘기면 컨텍스트를 많이 차지하고 비용도 커진다. jevfetch는 페이지를 블록 단위로 나누고, TypeSafe의 판정 모델 [Jev](https://docs.typesafe.ai)로 블록마다 질문에 답이 되는지 판단해, 답이 되는 블록만 원문 그대로 돌려준다.

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
# 8/133 blocks, 461 of 7141 tokens
## functools — Higher-order functions and operations on callable objects
Source code: [Lib/functools.py](https://github.com/python/cpython/tree/3.14/Lib/functools.py)
## functools — Higher-order functions and operations on callable objects > @functools.lru_cache(maxsize=128, typed=False)
Decorator to wrap a function with a memoizing callable that saves up to the maxsize most recent calls. ...
If maxsize is set to None, the LRU feature is disabled and the cache can grow without bound.
...
```

에이전트는 페이지 7,141토큰 중 461토큰만 받는다. `##` 줄은 바로 아래 발췌가 속한 제목 경로다. 함수 시그니처 같은 정의 목록 항목도 경로에 들어가므로, 에이전트는 `maxsize=None` 설명이 `lru_cache`에 대한 것임을 알 수 있다. 본문은 페이지에서 그대로 가져온다. jevfetch가 하는 일은 연속 공백을 하나로 줄이고, 링크를 `[텍스트](URL)`로 쓰고, 표 셀 사이에 ` | `를 넣고, 합친 목록 항목 앞에 `- `를 붙이고, `##` 줄을 추가하는 것뿐이다. JSON과 XML은 다시 직렬화하므로 공백, 이스케이프, 숫자 표기가 원본과 다를 수 있다(`1.10`은 `1.1`로 나온다). 캐시가 비어 있을 때 이 호출에 Jev 입력 37,327토큰(약 $0.0015)이 들었다.

| 상태 | 의미 | 종료 코드 |
|---|---|---|
| `filtered` | 임계값을 넘은 블록과 첫 블록. 첫 블록을 뺀 나머지가 300토큰 미만이면 점수가 높은 블록을 더 넣는다 | 0 |
| `passthrough` | 2,000토큰 이하의 짧은 페이지라 전체를 돌려준다 | 0 |
| `no_match` | 임계값을 넘은 블록이 없어 점수가 가장 높은 블록들을 돌려준다. 페이지에 답이 없다는 뜻은 아니다 | 0 |
| `empty` | 본문을 추출하지 못했다 | 0 |
| `fetch_error` | 페이지를 가져오지 못했거나, URL이 PDF나 이미지 같은 바이너리 파일이다. 바이너리 파일이면 오류 메시지에 content type이 나오고, `# saved:` 줄에 내려받은 파일의 경로가 나온다 | 1 |

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
- PDF나 이미지 같은 바이너리 파일. jevfetch는 HTML과 Markdown, JSON, XML 같은 텍스트 형식에서 구절을 고르고, 바이너리 응답은 Jev를 호출하지 않고 content type을 담은 `fetch_error`로 끝낸다. 에이전트가 Read로 열 수 있게 파일은 저장한다.

## 개인정보와 보안

- jevfetch는 페이지 텍스트와 질문을 TypeSafe API로 보낸다.
- Jev 응답은 `~/.cache/jevfetch`에 캐시된다(`JEVFETCH_CACHE_DIR`로 변경). 캐시는 언제 지워도 된다.
- PDF 같은 바이너리 파일은 시스템 임시 디렉터리의 `jevfetch-<UID>` 폴더에 저장된다(`JEVFETCH_FILES_DIR`로 변경).
- jevfetch는 받은 URL을 리다이렉트까지 따라가서 가져온다. 서비스로 운영한다면 가져올 수 있는 URL을 제한해야 한다.

## 동작 방식

1. 페이지를 가져온다. 정적 HTML의 본문이 200토큰 미만이면 헤드리스 Chrome으로 렌더링한다.
2. 페이지를 블록으로 나누고 블록마다 제목 경로를 붙인다. 내비게이션, 푸터 같은 영역은 버린다. 콜론으로 끝나는 문장은 같은 제목 아래 이어지는 목록 항목과 최대 1,500자까지 한 블록으로 합친다. 문장에 적힌 조건이 목록 항목과 떨어지지 않게 하려는 것이다. JSON은 키와 배열 원소 단위로, XML은 요소 단위로 나누고, 제목 경로 자리에 키나 태그 경로를 붙인다.
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
| `JEVFETCH_FILES_DIR` | 시스템 임시 디렉터리의 `jevfetch-<UID>` | 저장한 PDF 같은 바이너리 파일의 경로 |
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

## 이해관계 고지

jevfetch는 TypeSafe와 관계가 없다. a2sys는 TypeSafe에서 자금, 크레딧, 사전 접근 권한을 받지 않았다.

## 라이선스

[MIT](LICENSE)

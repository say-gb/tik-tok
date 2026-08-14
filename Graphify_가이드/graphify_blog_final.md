# 클로드 코드가 파일부터 뒤지지 않게 만드는 법 — Graphify 완전 가이드

**"질문 하나 했을 뿐인데 클로드가 파일 스무 개를 열어본다."**
큰 코드베이스에서 AI 코딩 도구를 써본 사람이라면 누구나 겪는 장면입니다. 검색 범위가 넓어질수록 컨텍스트는 커지고, 토큰은 새고, 답은 느려집니다.

Graphify는 이 문제를 다르게 풉니다. 코드의 함수, 클래스, 호출 관계를 미리 **지식 그래프**로 만들어 두고, 질문이 오면 전체 파일을 훑는 대신 필요한 연결만 먼저 꺼내보게 합니다.

다만 오해는 금물입니다. Graphify는 소스 코드를 영원히 읽지 않게 해주는 도구가 아닙니다. **그래프로 범위를 좁힌 뒤, 근거가 필요한 파일만 확인하게 만드는 도구**에 가깝습니다.

> **용어 한 줄 정리** — 지식 그래프는 함수·클래스·파일 같은 대상을 노드로, 호출·임포트·상속 같은 관계를 엣지로 저장한 지도입니다.

> [그래픽 1 — 전체 흐름 다이어그램]

## Graphify가 실제로 하는 일

- 코드 파일은 tree-sitter AST로 **로컬에서** 분석합니다. 코드 전용 실행에는 LLM 호출이 필요 없고, 코드가 외부 모델로 전송되지 않습니다.
- 문서, PDF, 이미지는 의미와 관계를 뽑는 과정에서 클로드 코드 세션의 모델이나 별도로 설정한 모델을 사용합니다.
- 영상과 음성은 선택 기능입니다(`uv tool install "graphifyy[video]"`). 전사는 faster-whisper로 로컬 처리되고, 만들어진 전사문을 그래프에 연결하는 의미 분석은 모델을 사용할 수 있습니다.
- 결과는 `graph.html`, `GRAPH_REPORT.md`, `graph.json`에 저장됩니다.
- 관계에는 `EXTRACTED`(소스에서 직접 발견), `INFERRED`(추론, 0.0~1.0 신뢰도 점수 포함), `AMBIGUOUS`(불확실, 수동 검토 대상) 태그가 붙습니다. 추론된 관계를 소스에서 직접 찾은 사실처럼 섞지 않기 위해서입니다.

---

## STEP 1. 준비물 확인 — 3분

Python 3.10 이상, uv, Claude Code가 필요합니다. macOS나 Linux 터미널에서는 아래 명령부터 실행하세요.

```bash
python3 --version
uv --version
claude --version
```

Windows PowerShell에서는 Python 명령이 보통 `python`입니다.

```
python --version
uv --version
claude --version
```

Python 버전이 3.10보다 낮거나 명령을 찾지 못하면 운영체제에 맞게 설치합니다.

macOS:

```bash
brew install python@3.12 uv
```

Windows:

```
winget install Python.Python.3.12
winget install astral-sh.uv
```

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y python3 python3-venv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치가 끝나면 터미널을 다시 열고 버전을 재확인하세요. Claude Code가 없다면 공식 안내에서 설치하고 로그인까지 끝냅니다.

확인 기준은 간단합니다.

- Python: `3.10` 이상
- uv: 버전 문자열 출력
- Claude Code: 버전 문자열 출력

---

## STEP 2. Graphify 설치 — 2분

여기서 가장 많이 틀리는 지점 하나. **공식 PyPI 패키지 이름은 `graphifyy`, y가 두 개입니다.** 설치 뒤 쓰는 명령은 `graphify`입니다. PyPI에 비슷한 이름의 다른 패키지들이 있는데 공식과 무관하니 헷갈리면 안 됩니다.

```bash
uv tool install graphifyy
graphify --version
graphify install
```

`graphify install`은 Claude Code가 `/graphify`를 알아보도록 사용자 영역에 스킬을 등록합니다. 버전 확인에서 `graphify 0.x.x`처럼 출력되면 CLI 설치가 끝난 겁니다.

`graphify: command not found`가 나오면 uv의 실행 경로를 셸에 추가합니다.

```bash
uv tool update-shell
```

터미널을 완전히 닫았다가 다시 열고 아래 두 줄을 재실행하세요.

```bash
graphify --version
graphify install
```

프로젝트 안에 스킬 설정을 넣어 팀과 함께 버전 관리하고 싶다면 프로젝트 루트에서 다음 명령을 대신 쓸 수 있습니다.

```bash
graphify install --project
```

개인 사용이라면 전역 `graphify install`이 가장 단순합니다.

> [스크린샷 2 — 설치 성공 화면] `graphify --version` 출력과 `Done. Open your AI coding assistant and type: /graphify .` 메시지가 한 화면에 보이도록 캡처

---

## STEP 3. 그래프에 넣을 파일 정리 — 3분

프로젝트 폴더로 이동합니다.

```bash
cd /path/to/your-project
```

Graphify는 `.gitignore`를 자동으로 따릅니다. 빌드 결과물이나 외부 의존성이 아직 제외되지 않았다면 프로젝트 루트에 `.graphifyignore`를 추가하세요. 문법은 `.gitignore`와 같고, 두 파일이 모두 있으면 병합되며 `.graphifyignore`가 우선합니다.

```
# .graphifyignore
node_modules/
dist/
build/
coverage/
.next/
.venv/
vendor/
*.min.js
```

소스 폴더를 무작정 제외하면 그래프가 틀어집니다. 테스트도 처음부터 빼지 마세요. 테스트 팩토리와 목 객체가 핵심 노드를 도배할 때만 `tests/`나 `__tests__/` 제외를 검토하면 됩니다.

어떤 파일을 빼야 할지 모르겠다면 Claude Code에 이 프롬프트를 붙여넣으세요.

```
이 저장소에서 생성물, 캐시, 외부 의존성만 골라 .graphifyignore 후보를 제안해줘.
실제 소스, 설정, 마이그레이션, 테스트는 임의로 제외하지 마.
파일은 아직 수정하지 말고 후보와 이유만 보여줘.
```

> [그래픽 3 — O·X 비교]

---

## STEP 4. 첫 지식 그래프 만들기 — 프로젝트에 따라 1~10분

프로젝트 루트에서 Claude Code를 엽니다.

```bash
claude
```

Claude Code 입력창에 아래 명령을 넣습니다. 이 줄은 일반 터미널 명령이 아니라 Claude Code 안에서 실행하는 슬래시 명령입니다.

```
/graphify .
```

기본 실행부터 권장합니다. `--mode deep`은 문서와 코드 사이의 의미 관계를 더 적극적으로 뽑고 싶을 때만 씁니다.

```
/graphify . --mode deep
```

코드 전용 프로젝트는 AST로 로컬 분석되므로 별도 API 키가 필요 없습니다. 문서, PDF, 이미지가 섞여 있으면 현재 Claude Code 세션의 모델이 의미 분석을 맡을 수 있습니다.

파일이 아주 많으면 Graphify가 범위를 줄일지 물을 수 있습니다. 이때 애플리케이션 소스가 있는 폴더부터 고르면 됩니다. 작은 프로젝트라면 바로 끝까지 진행됩니다.

첫 실행이 끝나면 프로젝트 루트에 다음 결과가 생깁니다.

```
graphify-out/
├── graph.html
├── GRAPH_REPORT.md
└── graph.json
```

- `graph.html`: 브라우저에서 노드와 연결을 클릭하는 시각화
- `GRAPH_REPORT.md`: 핵심 노드, 커뮤니티, 의외의 연결, 추천 질문
- `graph.json`: 이후 쿼리가 읽는 영속 그래프

> [그래픽 4 — 결과물 3종 시각화]

---

## STEP 5. 생성 결과 확인 — 2분

macOS나 Linux에서는 세 파일이 비어 있지 않은지 확인할 수 있습니다.

```bash
test -s graphify-out/graph.json && echo "graph.json OK"
test -s graphify-out/GRAPH_REPORT.md && echo "report OK"
test -s graphify-out/graph.html && echo "graph.html OK"
```

브라우저로 그래프를 엽니다.

macOS:

```bash
open graphify-out/graph.html
```

Linux:

```bash
xdg-open graphify-out/graph.html
```

Windows PowerShell:

```
start graphify-out/graph.html
```

`GRAPH_REPORT.md`에서는 노드 수, 엣지 수, 커뮤니티 수를 먼저 봅니다. 핵심 노드가 실제 도메인 클래스나 주요 함수가 아니라 테스트 헬퍼와 생성 코드뿐이라면 STEP 3의 제외 목록을 손본 뒤 다시 빌드해야 합니다.

노드 하나를 실제 소스와 대조해보세요. 보고서나 `graph.html`에서 클래스 또는 함수 이름을 고른 뒤 Claude Code에 입력합니다.

```
/graphify explain "실제 클래스나 함수 이름"
```

출력에 소스 파일, 줄 위치, 연결 관계와 신뢰도 태그가 나오면 쿼리까지 정상입니다.

> [스크린샷 5 — 실제 그래프 결과] `graph.html`에서 핵심 노드 하나를 선택하고 오른쪽 패널에 연결 노드와 커뮤니티가 보이는 화면

---

## STEP 6. Claude Code가 그래프부터 보게 만들기 — 1분

첫 그래프를 만든 뒤 프로젝트 루트에서 한 번 실행합니다.

```bash
graphify claude install
```

이 명령은 프로젝트의 CLAUDE.md 지시 파일과 PreToolUse 훅을 설정합니다. Claude가 검색하거나 소스 파일을 하나씩 열기 전에 `graphify query`, `graphify explain`, `graphify path`로 먼저 범위를 좁히도록 알려줍니다.

훅은 파일 읽기를 차단하지 않습니다. 그래프를 먼저 보고 필요한 원문만 열라는 **순서**를 추가할 뿐입니다. 정확한 구현이나 수정 지점은 마지막에 소스 파일로 재확인해야 합니다.

Graphify의 출력 때문에 Claude Code 프롬프트 캐시가 매번 무효화되는 일을 줄이려면 프로젝트의 `.claudeignore`에 다음 줄을 추가합니다.

```
# .claudeignore
graph.json
graphify-out/
```

`.claudeignore`는 Git 추적 여부를 바꾸지 않습니다. Git에서 결과물을 관리할지는 별도로 결정하세요.

항상 그래프부터 확인시키고 싶을 때 쓸 프롬프트입니다.

```
이 질문은 먼저 Graphify로 범위를 좁혀줘.
관련 노드와 경로를 찾은 뒤 근거가 필요한 소스 파일만 열고 파일과 줄 위치를 붙여 답해줘.
질문: [여기에 코드베이스 질문]
```

> [그래픽 6 — 적용 전후 비교]

---

## STEP 7. query, path, explain 제대로 쓰기 — 5분

세 명령의 역할이 다릅니다.

| 명령 | 언제 쓰는지 | 결과 |
| --- | --- | --- |
| `query` | 흐름이나 구조를 넓게 찾을 때 | 질문과 가까운 서브그래프 |
| `path` | 두 클래스·함수 사이 연결을 찾을 때 | 최단 연결 경로 |
| `explain` | 노드 하나의 역할을 볼 때 | 소스 위치와 주변 연결 |

> [그래픽 7 — 명령 선택표]

### 넓은 흐름 찾기

```
/graphify query "인증 요청이 데이터베이스까지 가는 흐름"
```

특정 체인을 깊게 따라가고 싶으면 DFS와 출력 예산을 붙입니다.

```
/graphify query "결제 실패가 재시도되는 흐름" --dfs --budget 1500
```

### 두 지점 사이 연결 찾기

아래 이름은 예시입니다. 실제 프로젝트의 클래스나 함수 이름으로 바꿔야 합니다.

```
/graphify path "AuthService" "UserRepository"
```

### 노드 하나 파악하기

```
/graphify explain "AuthService"
```

### 터미널에서 직접 조회하기

그래프가 이미 만들어졌다면 Claude Code를 열지 않고도 같은 데이터를 조회할 수 있습니다.

```bash
graphify query "show the auth flow"
graphify path "AuthService" "UserRepository"
graphify explain "AuthService"
```

한국어 질문이 원하는 노드를 못 찾으면 코드에 실제로 적힌 영문 심볼을 함께 넣으세요. Graphify CLI의 노드 매칭은 그래프에 들어 있는 어휘를 중심으로 작동합니다.

```
/graphify query "로그인 인증 AuthService UserRepository"
```

### 온보딩에 쓰는 프롬프트

```
Graphify에서 핵심 노드와 커뮤니티를 먼저 확인해줘.
이 프로젝트의 진입점, 주요 요청 흐름, 데이터 저장 경로를 설명하고 각 설명에 근거 파일과 줄 위치를 붙여줘.
INFERRED 관계는 추론이라고 표시해줘.
```

### 변경 영향 범위에 쓰는 프롬프트

```
[바꾸려는 클래스나 함수]를 수정하기 전에 Graphify로 연결된 호출자와 의존 대상을 찾아줘.
직접 연결과 간접 연결을 구분하고 실제 수정 전에 열어봐야 할 파일만 우선순위대로 보여줘.
```

### 버그 추적에 쓰는 프롬프트

```
[에러 증상]과 관련된 노드를 Graphify query로 찾고 요청이 실패 지점까지 가는 경로를 추적해줘.
EXTRACTED 엣지를 우선하고 INFERRED 엣지는 소스에서 다시 확인해줘.
```

### 설계 이유 찾기에 쓰는 프롬프트

```
Graphify에서 [기능 이름]과 연결된 NOTE, WHY, ADR, RFC 근거를 찾아줘.
무엇을 하는지보다 왜 이렇게 설계했는지 중심으로 설명하고 출처 파일을 붙여줘.
```

---

## STEP 8. 코드가 바뀐 뒤 그래프 갱신 — 1~5분

Graphify는 한 번 만들고 영원히 끝나는 도구가 아닙니다. 코드가 바뀌면 그래프도 갱신해야 합니다. 변경된 파일만 다시 처리하려면 Claude Code에서 실행합니다.

```
/graphify . --update
```

Git 커밋 뒤 코드 그래프를 자동으로 갱신하고 싶다면 프로젝트 루트에서 훅을 설치합니다.

```bash
graphify hook install
```

이 명령은 post-commit과 post-checkout 훅을 설치해 커밋 뒤 코드 변경을 AST로 다시 읽습니다. `graph.json`의 병합 충돌을 자동으로 합쳐주는 Git 머지 드라이버도 함께 설정됩니다. 문서나 이미지가 바뀌었을 때는 `/graphify . --update`를 직접 실행해야 합니다.

코드 저장 때마다 자동 반영하고 싶다면 별도 터미널에서 watch 모드를 쓸 수 있습니다.

```
/graphify . --watch
```

Graphify를 업데이트한 뒤에는 스킬과 Git 훅도 새 버전의 실행 경로로 다시 맞춥니다. 특히 Git 훅은 설치 시점의 인터프리터 경로를 내장하므로 업그레이드 후 재실행이 공식 권장사항입니다.

```bash
uv tool upgrade graphifyy
graphify install
graphify hook install
```

---

## STEP 9. 개인정보와 비용 범위 확인 — 2분

| 입력 | 기본 처리 | 외부 모델 사용 가능성 |
| --- | --- | --- |
| 코드 | tree-sitter AST, 로컬 | 코드 전용 기본 경로에서는 없음 |
| Markdown·텍스트 | 의미 분석 | 있음 |
| PDF·이미지 | 변환·의미 분석 | 있음 |
| 영상·음성 | 로컬 전사(faster-whisper) 후 의미 분석 | 전사문 분석에서 있음 |

코드 전용 저장소는 별도 API 키 없이 실행할 수 있습니다. 문서와 이미지는 현재 AI 코딩 어시스턴트의 모델이 내용을 읽을 수 있으니 외부 전송이 금지된 자료는 넣지 마세요. `.env`, 개인 키, 고객 데이터처럼 민감한 파일은 `.gitignore`와 `.graphifyignore`에서 다시 확인하는 편이 안전합니다.

Graphify는 결과물을 로컬 `graphify-out/`에 저장하고 텔레메트리, 사용 추적, 애널리틱스를 보내지 않는다고 밝히고 있습니다. 다만 `query`, `path`, `explain` 호출 기록은 로컬 파일(`~/.cache/graphify-queries.log`)에 남습니다. 외부 전송은 아니지만 남기고 싶지 않다면 `GRAPHIFY_QUERY_LOG_DISABLE=1`로 끌 수 있습니다. 그리고 사내 보안 정책이 있다면 도구 설명보다 회사 정책이 우선입니다.

---

## STEP 10. 토큰 절감 수치 바로 이해하기 — 2분

"설치하면 토큰이 무조건 70% 줄어든다"는 보장 수치는 공식 자료에 없습니다. 절감 폭은 프로젝트 크기와 질문 방식에 따라 크게 달라집니다.

공식 문서(how-it-works)의 재현 예시는 이렇습니다.

- 52파일 혼합 코퍼스(Karpathy 저장소 + 논문 5편 + 이미지 4장): 원본 전체를 매번 넣는 방식 대비 쿼리당 **71.5배** 적은 토큰
- 4파일 혼합 코퍼스(graphify 소스 + Transformer 논문): **5.4배**
- 6파일 소형 Python 코퍼스(httpx 합성 예제): **약 1배**

작은 저장소는 원래 컨텍스트에 들어가므로 압축 이득이 거의 없습니다. 큰 저장소에서 매 질문마다 전체를 넣는 대신 컴팩트한 서브그래프부터 꺼낼 때 차이가 커집니다. 첫 그래프 생성에는 토큰이 들고, 절감은 이후 쿼리부터 누적된다는 점도 기억하세요.

따라서 개인 성과를 말하려면 Graphify 실행 전후의 실제 사용량을 같은 작업으로 재야 합니다. 설치만으로 70% 절감을 확정하면 안 됩니다.

Graphify가 해결하는 것도 "클로드가 매번 모든 파일을 반드시 읽는다"는 동작 자체가 아닙니다. 넓은 검색과 불필요한 파일 열기를 줄이고, 그래프에서 관련 범위를 찾은 뒤 원문을 확인하게 만드는 방식입니다.

> [그래픽 8 — 수치 비교 차트]

---

## STEP 11. 문제가 생겼을 때 바로 고치기 — 3분

### `graphify: command not found`

```bash
uv tool update-shell
```

터미널을 다시 열고 확인합니다.

```bash
graphify --version
```

### `ModuleNotFoundError: No module named 'graphify'`

plain pip와 다른 Python 환경이 섞인 경우가 많습니다. uv 도구 환경으로 다시 설치합니다.

```bash
uv tool uninstall graphifyy
uv tool install graphifyy
graphify install
```

### `/graphify`를 Claude Code가 못 알아봄

```bash
graphify install
```

Claude Code를 완전히 종료한 뒤 프로젝트 루트에서 다시 엽니다.

### `graphify extract .`을 실행했는데 `graph.json`만 생김

`graphify extract`는 CI나 헤드리스 실행에 가까운 CLI 경로입니다. 보고서와 HTML까지 만들려면 다음 명령을 이어서 실행합니다.

```bash
graphify cluster-only .
```

처음부터 Claude Code 안에서 `/graphify .`을 쓰면 기본 파이프라인이 `GRAPH_REPORT.md`와 `graph.html`까지 만듭니다.

### 쿼리 결과가 0개거나 엉뚱함

질문에 실제 함수명과 클래스명을 넣습니다.

```
/graphify query "한국어 질문 ActualClassName actual_function"
```

그래프가 오래됐다면 먼저 갱신합니다.

```
/graphify . --update
```

### 테스트 헬퍼가 핵심 노드를 도배함

`.graphifyignore`에 테스트 폴더를 추가한 뒤 전체를 다시 만듭니다. 테스트가 실제 설계 근거를 담고 있다면 전부 제외하지 말고 문제가 되는 하위 폴더만 좁혀서 제외하세요.

```
# .graphifyignore
tests/fixtures/
tests/generated/
```

```bash
graphify extract . --force
graphify cluster-only .
```

### watch 모드에서 의존성 오류가 남

먼저 최신 버전으로 올려서 재시도합니다.

```bash
uv tool upgrade graphifyy
```

그래도 안 되면 전체 선택 기능을 포함해 재설치할 수 있습니다.

```bash
uv tool install "graphifyy[all]"
```

### Windows PowerShell에서 `/graphify .`이 경로 오류로 처리됨

PowerShell은 맨 앞 슬래시를 경로 구분자로 해석합니다. 터미널에서는 슬래시 없이 씁니다.

```
graphify .
```

Claude Code 입력창에서는 원래대로 `/graphify .`을 사용합니다.

### 제거하고 싶음

프로젝트의 Claude Code 연동만 제거합니다.

```bash
graphify claude uninstall
```

설치된 Graphify 스킬을 모든 플랫폼에서 제거합니다.

```bash
graphify uninstall
```

결과물(`graphify-out/`)까지 지우는 명령은 되돌리기 어렵습니다.

```bash
graphify uninstall --purge
```

---

## 마지막 점검

- `graphify --version`이 출력된다.
- Claude Code에서 `/graphify .`이 실행된다.
- `graphify-out/graph.json`, `GRAPH_REPORT.md`, `graph.html`이 생겼다.
- `graphify explain "실제 심볼"`이 소스 위치와 연결을 보여준다.
- `graphify claude install`로 쿼리 우선 흐름을 적용했다.
- 코드 변경 뒤 `/graphify . --update`나 Git 훅으로 그래프를 갱신한다.
- INFERRED 관계는 실제 소스에서 다시 확인한다.

## 공식 근거

- [Graphify 공식 저장소 (GitHub, Graphify-Labs/graphify)](https://github.com/Graphify-Labs/graphify)
- [Graphify 공식 PyPI 패키지 (graphifyy)](https://pypi.org/project/graphifyy/)
- [Graphify 공식 사이트](https://graphify.net/)
- [동작 원리와 공개 토큰 예시 (docs/how-it-works.md)](https://github.com/Graphify-Labs/graphify/blob/v8/docs/how-it-works.md)
- [공개 벤치마크와 재현 조건 (BENCHMARKS.md)](https://github.com/Graphify-Labs/graphify/blob/v8/BENCHMARKS.md)

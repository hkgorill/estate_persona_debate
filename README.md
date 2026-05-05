# 페르소나 멀티 에이전트 데모 (`estate_persona_debate`)

[Streamlit](https://streamlit.io/) **멀티페이지** 앱입니다. 실행 후 **좌측 사이드바**(또는 좁은 화면에서는 상단 메뉴)에서 페이지를 선택합니다.

**저장소:** [https://github.com/hkgorill/estate_persona_debate](https://github.com/hkgorill/estate_persona_debate)

---

## 페이지 구성 (메뉴 순서)

| 구분 | 파일 | 설명 |
|:---:|:---|:---|
| **홈** | `app.py` | 서비스 안내, 폴더·모듈 구조 요약 |
| **1** | `pages/1_부동산_심의.py` | 부동산 주소·물건 정보 입력 → **시장분석가 · 비관론자 · 세무/재무 · 의장** 응답을 **통합 단일 호출**로 생성 → 종합 투자 의견 포함 |
| **2** | `pages/2_기사_TEXT_논평.py` | 기사 **본문**(필수)·**링크**(선택) → **조언자 3명**(프리셋 또는 기타) + 종합 메모를 **통합 단일 호출**로 생성 |
| **3** | `pages/3_주식_기사_석학논평.py` | 주식 기사 **본문**(필수)·**링크**(선택) → **조언자 3명**(프리셋 또는 기타) + 종합 메모를 **통합 단일 호출**로 생성 |
| **4** | `pages/4_유튜브_요약.py` | 유튜브 **URL** → 자막 수집 → **Gemini** 요약 |

**안내**

- 부동산 결과는 **참고용 시뮬레이션**이며 법률·세무·투자 자문이 아닙니다.
- 일반·주식 기사 논평은 **페르소나 역할 연기**이며 실제 인물의 발언이 아닙니다.
- **주식 페이지 출력은 투자 자문·특정 종목 매매 추천이 아닙니다.**
- 기사 URL만 입력해도 **본문은 자동으로 가져오지 않습니다.** 저작권·이용약관 이슈를 피하기 위해 텍스트는 사용자가 직접 붙여 넣는 방식입니다.

---

## 기술 스택

| 구분 | 사용 |
|------|------|
| 언어 | Python 3.11+ 권장 |
| UI | Streamlit (multipage: `app.py` + `pages/`) |
| LLM | LangChain + Google Gemini (`langchain-google-genai`) |
| API 키 | 로컬 `.env` 또는 Streamlit Community Cloud **Secrets** |

**Gemini 모델:** 사이드바에서 선택합니다. 기본 목록은 `gemini_common.py`의 `GEMINI_MODEL_OPTIONS`와 동일하며, 비용 절감을 위해 **`gemini-2.5-flash-lite`** 가 첫 번째(기본값)입니다. Google 정책상 **`gemini-2.0-flash`는 일부 API 키·프로젝트에서 더 이상 쓰이지 않을 수 있어** 목록에서 빠져 있습니다. 404가 나면 **다른 모델**(예: `gemini-2.5-pro`, `gemini-1.5-pro`)을 고르세요.

**토큰 절감 (통합 호출):** 페이지 **1·2·3**은 긴 입력(물건 정보·기사 본문)을 역할마다 반복 전송하지 않고, **한 번의 모델 응답** 안에 구간 태그(`###MARKET###`, `###P1###` 등)로 나눠 파싱합니다. 출력 형식 오류 시 해당 페이지에서 **다시 실행**하면 됩니다.

의존성 목록은 [`requirements.txt`](./requirements.txt)를 참고하세요.

---

## 사전 준비

- [Python 3.11+](https://www.python.org/downloads/)
- [Google AI Studio](https://aistudio.google.com/apikey)에서 발급한 Gemini API 키

Windows에서 `pip` / `streamlit` 명령을 찾지 못하면 아래처럼 **`python -m`** 형태를 사용합니다.

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

(`python` 대신 `py -m ...`만 동작하는 환경도 있습니다.)

---

## 설치

```powershell
git clone https://github.com/hkgorill/estate_persona_debate.git
cd estate_persona_debate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 환경 변수 (로컬)

1. 프로젝트 루트에 `.env` 생성 (**Git에는 커밋하지 않음**, `.gitignore` 처리됨).
2. 아래 **중 하나**를 설정합니다.

```env
GOOGLE_API_KEY=발급받은_키
```

또는:

```env
GEMINI_API_KEY=발급받은_키
```

템플릿은 [`.env.example`](./.env.example)입니다.

```powershell
Copy-Item .env.example .env
# .env 편집 후 실제 키 입력
```

앱 코드는 `gemini_common.py`에서 위 변수와 Streamlit Secrets를 모두 인식합니다.

### Notion·Google Sheets 기록 (선택)

Notion·Sheets가 설정되어 있으면 1~4 페이지에서 **LLM 실행이 성공한 직후** 자동으로 저장됩니다. (버튼 없음)

| 저장소 | 내용 |
|--------|------|
| **Notion** | 질문(요약)·요약 답변·세션 ID·모델 등 |
| **Google Sheets** | 입력·출력 **전체**(셀 길이 초과 시 같은 `session_id`로 여러 행) |

**당신이 미리 할 작업**

1. **Notion**
   - [Developers](https://www.notion.so/my-integrations)에서 Integration 생성 → **Internal Integration Secret** 복사 (`NOTION_TOKEN`).
   - 새 **데이터베이스**를 만들고 아래 **프로퍼티**를 동일한 이름·타입으로 추가합니다.
     - **Name** (제목)
     - **페이지** (선택) — 옵션을 정확히 추가: `1 부동산`, `2 기사`, `3 주식`, `4 유튜브`
     - **질문**, **요약 답변**, **세션 ID**, **모델** (본문)
     - **토큰 입력**, **토큰 출력**, **토큰 합계** (숫자 — LangChain `usage_metadata` 합계, 청구 단위와 다를 수 있음)
     - **실행일시** (날짜: 시간 포함)
   - 데이터베이스 페이지 **⋯ → 연결(Connections)** 에서 위 Integration 을 연결합니다.
   - DB URL 에서 **데이터베이스 ID**를 복사해 `NOTION_DATABASE_ID`에 넣습니다.

2. **Google Sheets**
   - Google Cloud 프로젝트에서 **Google Sheets API** 활성화 → **서비스 계정** 생성 → **JSON 키** 다운로드.
   - 새 스프레드시트를 만들고, **1행**에 아래 **헤더**(영문·순서 고정)를 입력합니다.  
     `session_id`, `created_at`, `page`, `model_name`, `temperature`, `part`, `input_full`, `output_full`, `input_tokens`, `output_tokens`, `total_tokens`  
     (기존 시트에 열이 없으면 **위 순서대로** 새 열을 추가하세요. 같은 `session_id`로 여러 행이 생길 때 토큰 값은 **첫 행(part 0)** 에만 채워지고 나머지는 비워 둡니다.)
   - 스프레드시트 **공유**에 서비스 계정 이메일(`…@…iam.gserviceaccount.com`)을 **편집자**로 추가합니다.
   - `GOOGLE_SHEETS_SPREADSHEET_ID`에는 스프레드시트 **ID** 또는 브라우저 **URL 전체**를 넣을 수 있습니다. 서비스 계정은 **`GOOGLE_SHEETS_CREDENTIALS_PATH`(파일 경로)** 가 가장 안정적입니다. `.env` 한 줄 JSON(`GOOGLE_SHEETS_CREDENTIALS_JSON`)은 따옴표·이스케이프 때문에 실패하기 쉬우며, 그럴 때는 **`GOOGLE_SHEETS_CREDENTIALS_JSON_B64`**(JSON 파일을 Base64 인코딩) 또는 파일 경로만 쓰면 됩니다. 인라인 JSON을 여러 줄로 넣으면 **그 아래 줄의 환경 변수가 통째로 로드되지 않을 수 있으므로**, 문제가 나면 `GOOGLE_SHEETS_CREDENTIALS_JSON` 항목을 **비우거나 삭제**하고 경로 변수만 두는 것이 안전합니다. **Windows 사용자 환경 변수**에 예전에 넣어 둔 `GOOGLE_SHEETS_CREDENTIALS_JSON` 은 주석 처리만으로는 사라지지 않습니다. `.env`에 빈 줄 `GOOGLE_SHEETS_CREDENTIALS_JSON=` 을 두면 앱이 해당 키를 비우도록 덮어씁니다.

`.env` 예시는 [`.env.example`](./.env.example)에 있습니다. Streamlit Cloud 는 **Secrets**에 동일 키명으로 넣으면 됩니다.

---

## Streamlit Community Cloud (배포 시)

- 저장소를 연결한 뒤 **Main file**은 `app.py`로 두면 됩니다.
- API 키는 로컬 `.env`가 배포에 포함되지 않으므로, 대시보드 **Secrets**에 예시처럼 넣습니다.

```toml
GOOGLE_API_KEY = "여기에_키"
# 선택: Notion / Sheets 기록
# NOTION_TOKEN = "secret_…"
# NOTION_DATABASE_ID = "…"
# GOOGLE_SHEETS_SPREADSHEET_ID = "…"
# GOOGLE_SHEETS_CREDENTIALS_JSON = """{…서비스 계정 JSON…}"""
# GOOGLE_SHEETS_CREDENTIALS_JSON_B64 = "…Base64…"
```

저장 후 **재배포(Redeploy)** 하면 각 페이지에서 동일하게 키가 로드됩니다.

---

## 실행

```powershell
python -m streamlit run app.py
```

브라우저에서 표시되는 주소(기본 `http://localhost:8501`)로 접속합니다.

각 기능 페이지의 **사이드바**에서 Gemini 모델과 온도(창의성)를 바꿀 수 있습니다.

---

## 코드 구조 (리팩터링 요약)

| 파일 | 역할 |
|------|------|
| `app.py` | 홈 UI만 담당 (진입점) |
| `gemini_common.py` | API 키 로드(`.env` + `st.secrets`), `make_llm`, 사이드바 모델 설정 UI, 공통 에러 힌트 |
| `debate_estate.py` | 부동산 위원 **시스템 프롬프트** 및 LangChain 체인 (UI 없음) |
| `persona_presets.py` | 기사·주식 논평용 페르소나 **프리셋 각 10명** + **기타** 지침 래핑, 사회자 시스템 프롬프트 |
| `article_persona_chains.py` | 기사 본문 논평·라벨 기반 종합 메모용 LangChain 체인 |
| `pages/*.py` | 페이지별 Streamlit UI (2·3번은 Selectbox로 조합 선택) |

새 기능을 추가할 때는 **`pages/`에 페이지 추가** + 필요 시 **`gemini_common` + 도메인 모듈** 패턴을 따르면 됩니다.

---

## 디렉터리 트리

```
estate_persona_debate/
├── app.py
├── gemini_common.py
├── debate_estate.py
├── persona_presets.py
├── article_persona_chains.py
├── session_export.py
├── youtube_transcript_util.py
├── pages/
│   ├── 1_부동산_심의.py
│   ├── 2_기사_TEXT_논평.py
│   ├── 3_주식_기사_석학논평.py
│   └── 4_유튜브_요약.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── .github/workflows/ci.yml
```

---

## CI/CD (GitHub Actions)

| 항목 | 내용 |
|------|------|
| 파일 | [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) |
| 트리거 | 브랜치 `main` 또는 `master`에 대한 `push`, `pull_request` |
| 작업 | 의존성 설치 후 루트 모듈(`persona_presets.py`, `article_persona_chains.py` 등) `py_compile` 및 `pages/` `compileall` |

CI에서는 **Gemini API를 호출하지 않습니다.** 따라서 GitHub 저장소에 API 키 시크릿을 넣을 필요는 없습니다.

### 원격 저장소에 처음 푸시할 때 (예시)

```powershell
cd estate_persona_debate
git init
git add .
git commit -m "feat: multipage Streamlit + Gemini personas"
git branch -M main
git remote add origin https://github.com/hkgorill/estate_persona_debate.git
git push -u origin main
```

---

## 민감 정보 (`.gitignore`)

커밋에서 제외하는 예시는 다음과 같습니다.

- `.env`, `.env.*` (예시만 허용: `!.env.example`)
- Python 가상환경 (`venv/`, `.venv/` 등)
- `.streamlit/secrets.toml` (로컬 시크릿 파일을 쓰는 경우)
- 키 파일 패턴 (`*.pem`, `*.key` 등)

키가 공개 저장소 등에 노출된 경우 [AI Studio](https://aistudio.google.com/apikey)에서 해당 키를 **폐기·재발급**하세요.

---

## 라이선스

필요 시 저장소 루트에 `LICENSE` 파일을 추가하면 됩니다.

---

## 이슈

[Issues](https://github.com/hkgorill/estate_persona_debate/issues)

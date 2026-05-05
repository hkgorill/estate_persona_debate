# 페르소나 멀티 에이전트 데모 (`estate_persona_debate`)

[Streamlit](https://streamlit.io/) **멀티페이지** 앱입니다. 실행 후 **좌측 사이드바**(또는 좁은 화면에서는 상단 메뉴)에서 페이지를 선택합니다.

**저장소:** [https://github.com/hkgorill/estate_persona_debate](https://github.com/hkgorill/estate_persona_debate)

---

## 페이지 구성 (메뉴 순서)

| 구분 | 파일 | 설명 |
|:---:|:---|:---|
| **홈** | `app.py` | 서비스 안내, 폴더·모듈 구조 요약 |
| **1** | `pages/1_부동산_심의.py` | 부동산 주소·물건 정보 입력 → **시장분석가 · 비관론자 · 세무/재무** 순차 발언 → 종합 투자 의견 |
| **2** | `pages/2_기사_TEXT_논평.py` | 기사 **본문**(필수)·**링크**(선택) → **조언자 3명** 각각 **프리셋 10인**(맹자·순자·쇼펜하우어·노자 등) 또는 **기타(직접 입력)** 선택 → 순차 논평 → 종합 메모 |
| **3** | `pages/3_주식_기사_석학논평.py` | 주식 기사 **본문**(필수)·**링크**(선택) → **조언자 3명** 각각 **프리셋 10인**(버핏·그레이엄·린치·케인스 등) 또는 **기타** → 순차 논평 → 종합 메모 |
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

1~4 페이지 실행 후 **「Notion·Google Sheets에 기록」** 버튼으로 저장할 수 있습니다.

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
     - **실행일시** (날짜: 시간 포함)
   - 데이터베이스 페이지 **⋯ → 연결(Connections)** 에서 위 Integration 을 연결합니다.
   - DB URL 에서 **데이터베이스 ID**를 복사해 `NOTION_DATABASE_ID`에 넣습니다.

2. **Google Sheets**
   - Google Cloud 프로젝트에서 **Google Sheets API** 활성화 → **서비스 계정** 생성 → **JSON 키** 다운로드.
   - 새 스프레드시트를 만들고, **1행**에 아래 **헤더**(영문·순서 고정)를 입력합니다.  
     `session_id`, `created_at`, `page`, `model_name`, `temperature`, `part`, `input_full`, `output_full`
   - 스프레드시트 **공유**에 서비스 계정 이메일(`…@…iam.gserviceaccount.com`)을 **편집자**로 추가합니다.
   - 스프레드시트 URL의 **ID**를 `GOOGLE_SHEETS_SPREADSHEET_ID`에 넣고, JSON 은 `GOOGLE_SHEETS_CREDENTIALS_PATH`(파일 경로) 또는 `GOOGLE_SHEETS_CREDENTIALS_JSON`(전체 JSON 문자열)로 지정합니다.

`.env` 예시는 [`.env.example`](./.env.example)에 있습니다. Streamlit Cloud 는 **Secrets**에 동일 키명으로 넣으면 됩니다.

---

---

##[트러블슈팅팅]Gemini API 과금 정책, Google Sheets API 연동 방법, 그리고 구글 클라우드 조직 정책 설정 과정

# Google API 연동 및 클라우드 설정 가이드

본 문서는 파이썬 프로젝트에서 **Gemini API**와 **Google Sheets API**를 효율적으로 연동하고, 구글 클라우드 콘솔(GCP)에서 발생하는 권한 및 조직 정책 문제를 해결하는 방법을 정리한 가이드입니다.

---

## 1. Gemini API 과금 정책 안내

### [구글 AI 스튜디오 무료 티어]
* **Gemini 2.0 Flash / 1.5 Flash:** 분당 15회(RPM), 일일 1,500회(RPD) 무료.
* **Gemini 1.5 Pro:** 분당 2회, 일일 50회 무료.
* **주의사항:** 구글 클라우드(GCP) 프로젝트에 결제 수단이 등록된 경우, 무료 한도를 초과하면 종량제 요금이 발생할 수 있습니다. (예: 22원 등의 소액 결제 발생)

---

## 2. Google Sheets API 연동 절차

### 1단계: API 활성화 및 서비스 계정 생성
1.  **Google Cloud Console** 접속 및 프로젝트 선택.
2.  **API 및 서비스 > 라이브러리:** `Google Sheets API` 및 `Google Drive API` 검색 후 **[사용]** 클릭.
3.  **IAM 및 관리 > 서비스 계정:** **[+ 서비스 계정 만들기]** 클릭 후 이름 설정 및 완료.

### 2단계: JSON 키 발급 및 시트 공유
1.  생성된 서비스 계정의 **[키]** 탭 이동 ➔ **[새 키 만들기]** ➔ **[JSON]** 선택 및 다운로드.
2.  다운로드된 JSON 파일 내 `client_email` 주소 복사.
3.  사용할 구글 시트의 **[공유]** 버튼 클릭 ➔ 복사한 이메일을 **'편집자'** 권한으로 추가.

---

## 3. 핵심 트러블슈팅: 조직 정책 및 권한 해결

### 이슈 1: "서비스 계정 키 생성 사용 중지됨" 팝업 발생
조직 보안 정책(`iam.disableServiceAccountKeyCreation`)이 키 생성을 차단한 경우입니다.
1.  콘솔 상단에서 **[조직(최상위 레벨)]**을 선택합니다.
2.  **IAM 및 관리 > 조직 정책** 메뉴로 이동합니다.
3.  `iam.disableServiceAccountKeyCreation` 제약 조건을 찾아 클릭합니다.
4.  **[정책 수정]** ➔ 맞춤설정 ➔ **[사용 안함(Off)]**으로 변경 후 저장합니다.

### 이슈 2: "정책 관리" 버튼이 비활성화된 경우
조직 정책을 수정할 수 있는 IAM 권한이 부족한 경우입니다.
1.  **조직 레벨**의 **IAM 및 관리 > IAM** 메뉴로 이동합니다.
2.  본인의 계정 옆 **[편집(연필 아이콘)]** 클릭.
3.  **[+ 다른 역할 추가]** 클릭 후 **`조직 정책 관리자(Organization Policy Administrator)`** 역할을 부여하고 저장합니다.
4.  새로고침(F5) 후 정책 수정을 다시 진행합니다.

---

## 4. Python 연동 코드 예시 (gspread)

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 권한 범위 및 인증 설정
scope = ["[https://spreadsheets.google.com/feeds](https://spreadsheets.google.com/feeds)", "[https://www.googleapis.com/auth/drive](https://www.googleapis.com/auth/drive)"]
creds = ServiceAccountCredentials.from_json_keyfile_name("your-key.json", scope)
client = gspread.authorize(creds)

# 시트 열기 (URL 방식 추천)
sheet = client.open_by_url("YOUR_SPREADSHEET_URL").sheet1

# 데이터 쓰기
sheet.update(range_name="A1", values=[["Hello", "Google API"]])
```

---

## 5. 보안 및 관리 수칙
* **JSON 키 파일 보안:** `.json` 키 파일은 절대 GitHub 등 퍼블릭 저장소에 업로드하지 마세요. ( `.gitignore`에 추가 필수)
* **예산 알림 설정:** GCP 결제 메뉴의 **[예산 및 알림]**에서 월간 한도를 설정하여 예상치 못한 과금을 방지하세요.

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

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

---

## Streamlit Community Cloud (배포 시)

- 저장소를 연결한 뒤 **Main file**은 `app.py`로 두면 됩니다.
- API 키는 로컬 `.env`가 배포에 포함되지 않으므로, 대시보드 **Secrets**에 예시처럼 넣습니다.

```toml
GOOGLE_API_KEY = "여기에_키"
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

# 부동산 가상 투자 심의 위원회 (estate_persona_debate)

부동산 주소·물건 정보를 입력하면 **가상 위원 3인**(시장분석가 📈, 비관론자 ⚠️, 세무·재무 전문가 💰)이 **순차적으로** 분석하고, 마지막에 **종합 투자 의견 및 핵심 고려사항**을 요약해 보여 주는 [Streamlit](https://streamlit.io/) 웹 앱입니다.

**저장소:** [https://github.com/hkgorill/estate_persona_debate](https://github.com/hkgorill/estate_persona_debate)

> 본 프로젝트는 참고용 시뮬레이션이며, 법률·세무·투자 자문이 아닙니다.

---

## 기술 스택

| 구분 | 사용 |
|------|------|
| 언어 | Python 3.11+ 권장 |
| UI | Streamlit |
| LLM | LangChain + Google Gemini (`langchain-google-genai`) |
| API 키 | `.env` + `python-dotenv` (`GOOGLE_API_KEY` 또는 `GEMINI_API_KEY`) |

---

## 사전 준비

- Python 3.11 이상 ([python.org](https://www.python.org/downloads/))
- [Google AI Studio](https://aistudio.google.com/apikey)에서 발급한 Gemini API 키

Windows에서 `pip` / `streamlit`이 인식되지 않으면 `python -m pip`, `python -m streamlit` 형태를 사용하세요.

---

## 설치

```powershell
git clone https://github.com/hkgorill/estate_persona_debate.git
cd estate_persona_debate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

(`python` 대신 `py`만 동작하면 `py -m pip ...` 로 바꿔도 됩니다.)

---

## 환경 변수

1. 프로젝트 루트에 `.env` 파일 생성 (저장소에는 **커밋하지 않음** — `.gitignore` 적용)
2. 아래 중 하나를 설정:

```env
GOOGLE_API_KEY=발급받은_키
```

또는:

```env
GEMINI_API_KEY=발급받은_키
```

템플릿: [`.env.example`](./.env.example)

```powershell
Copy-Item .env.example .env
# .env 편집 후 실제 키 입력
```

---

## 실행

```powershell
python -m streamlit run app.py
```

브라우저에서 표시되는 주소(기본 `http://localhost:8501`)로 접속합니다.

---

## 프로젝트 구조

```
estate_persona_debate/
├── app.py                 # Streamlit 메인 (프롬프트·LangChain 체인·UI)
├── requirements.txt       # Python 의존성
├── .env.example           # 환경 변수 예시 (비밀 없음, 커밋 가능)
├── .gitignore             # 민감 정보·캐시 제외
├── README.md
└── .github/workflows/
    └── ci.yml             # GitHub Actions CI
```

---

## CI/CD (GitHub Actions)

| 항목 | 내용 |
|------|------|
| 워크플로 파일 | [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) |
| 트리거 | `main` / `master`에 대한 `push`, `pull_request` |
| 작업 | Python 3.11·3.12에서 `pip install -r requirements.txt` 후 `python -m py_compile app.py` |

**참고:** CI에서는 Gemini API를 호출하지 않으므로, GitHub에 API 키 시크릿을 넣을 필요는 없습니다.

### 저장소에 처음 올릴 때 (예시)

```powershell
cd estate_persona_debate
git init
git add .
git commit -m "Initial commit: Streamlit + LangChain + Gemini"
git branch -M main
git remote add origin https://github.com/hkgorill/estate_persona_debate.git
git push -u origin main
```

---

## 민감 정보 (.gitignore)

다음은 커밋에서 제외됩니다.

- `.env`, `.env.*` (단, `!.env.example`은 예외로 포함 가능)
- 가상환경 `venv/`, `.venv/` 등
- `.streamlit/secrets.toml`
- `*.pem`, `*.key` 등

키가 유출되었다면 [AI Studio](https://aistudio.google.com/apikey)에서 해당 키를 삭제하고 새로 발급하세요.

---

## 라이선스

필요 시 저장소 루트에 `LICENSE` 파일을 추가하세요.

---

## 이슈

[Issues](https://github.com/hkgorill/estate_persona_debate/issues)

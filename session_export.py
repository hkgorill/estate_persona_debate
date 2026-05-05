# -*- coding: utf-8 -*-
"""Notion(요약) + Google Sheets(전체) 기록. Streamlit Secrets / .env 지원."""

from __future__ import annotations

import base64
import binascii
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

from dotenv import load_dotenv

# 프로젝트 루트 `.env` (실행 cwd 와 무관하게 로드)
_REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(_REPO_ROOT / ".env")

_SHEETS_DOTENV_KEYS: Final[tuple[str, ...]] = (
    "GOOGLE_SHEETS_CREDENTIALS_PATH",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_SHEETS_SPREADSHEET_ID",
    "GOOGLE_SHEETS_CREDENTIALS_JSON",
    "GOOGLE_SHEETS_CREDENTIALS_JSON_B64",
)


def _overlay_sheets_keys_from_repo_dotenv_file() -> None:
    """`.env`에 명시된 Sheets 관련 키만 OS 값보다 우선 적용. `KEY=` 빈 값이면 OS 해당 키 제거."""
    try:
        from dotenv import dotenv_values
    except ImportError:
        return
    vals = dotenv_values(_REPO_ROOT / ".env")
    if not vals:
        return
    for k in _SHEETS_DOTENV_KEYS:
        if k not in vals:
            continue
        raw = vals[k]
        if raw is None:
            continue
        v = str(raw).strip()
        if v == "":
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

# Notion DB에 동일한 이름·타입으로 프로퍼티를 만들어야 합니다.
NOTION_PROP_NAME: Final[str] = "Name"  # Title
NOTION_PROP_PAGE: Final[str] = "페이지"  # Select
NOTION_PROP_QUESTION: Final[str] = "질문"  # Rich text
NOTION_PROP_SUMMARY: Final[str] = "요약 답변"  # Rich text
NOTION_PROP_DATETIME: Final[str] = "실행일시"  # Date
NOTION_PROP_SESSION: Final[str] = "세션 ID"  # Rich text
NOTION_PROP_MODEL: Final[str] = "모델"  # Rich text

NOTION_PAGE_OPTIONS: Final[tuple[str, ...]] = ("1 부동산", "2 기사", "3 주식", "4 유튜브")

SHEET_HEADERS: Final[tuple[str, ...]] = (
    "session_id",
    "created_at",
    "page",
    "model_name",
    "temperature",
    "part",
    "input_full",
    "output_full",
)

_MAX_NOTION_TEXT: Final[int] = 2000
_MAX_SHEET_CELL: Final[int] = 49_000


def _hydrate_export_secrets() -> None:
    _overlay_sheets_keys_from_repo_dotenv_file()
    try:
        import streamlit as st

        sec = st.secrets
        for key in (
            "NOTION_TOKEN",
            "NOTION_DATABASE_ID",
            "GOOGLE_SHEETS_SPREADSHEET_ID",
            "GOOGLE_SHEETS_CREDENTIALS_JSON",
            "GOOGLE_SHEETS_CREDENTIALS_JSON_B64",
            "GOOGLE_SHEETS_CREDENTIALS_PATH",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ):
            if key in sec and str(sec[key]).strip():
                os.environ.setdefault(key, str(sec[key]).strip())
    except Exception:
        pass


def _rich_text_prop(text: str) -> dict[str, Any]:
    t = text or ""
    parts: list[dict[str, Any]] = []
    if not t.strip():
        return {"rich_text": [{"type": "text", "text": {"content": " "}}]}
    while t:
        chunk = t[:_MAX_NOTION_TEXT]
        t = t[_MAX_NOTION_TEXT:]
        parts.append({"type": "text", "text": {"content": chunk}})
    return {"rich_text": parts}


def truncate_question_for_notion(text: str, max_len: int = 2000) -> str:
    s = (text or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def get_notion_token() -> str | None:
    _hydrate_export_secrets()
    t = os.getenv("NOTION_TOKEN")
    return t.strip() if t and t.strip() else None


def get_notion_database_id() -> str | None:
    _hydrate_export_secrets()
    d = os.getenv("NOTION_DATABASE_ID")
    return d.strip() if d and d.strip() else None


def _normalize_spreadsheet_id(raw: str | None) -> str | None:
    """순수 ID 또는 docs.google.com 전체 URL 모두 허용."""
    if not raw:
        return None
    s = raw.strip().strip('"').strip("'")
    if not s:
        return None
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", s)
    if m:
        return m.group(1)
    return s


def get_spreadsheet_id() -> str | None:
    _hydrate_export_secrets()
    return _normalize_spreadsheet_id(os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"))


def _parse_credentials_json_string(raw: str) -> dict[str, Any] | None:
    """`.env` 한 줄 JSON에서 자주 나는 따옴표·이스케이프·스마트 따옴표를 보정 후 파싱."""
    if not raw or not str(raw).strip():
        return None
    s0 = str(raw).strip().lstrip("\ufeff")
    s0 = (
        s0.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )

    candidates: list[str] = []
    seen: set[str] = set()

    def add(v: str) -> None:
        v = v.strip()
        if len(v) < 2 or v in seen:
            return
        seen.add(v)
        candidates.append(v)

    add(s0)
    s = s0
    for _ in range(2):
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
            s = s[1:-1].strip()
            add(s)
            add(s.replace('\\"', '"').replace("\\'", "'"))

    for c in list(candidates):
        if "\\n" in c:
            add(c.replace("\\n", "\n"))

    for cand in candidates:
        try:
            data = json.loads(cand)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    return None


def _load_credentials_from_path_env() -> dict[str, Any] | None:
    """GOOGLE_SHEETS_CREDENTIALS_PATH 또는 GOOGLE_APPLICATION_CREDENTIALS 파일."""
    path = (
        (os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH") or "").strip()
        or (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    )
    if not path:
        return None
    p = path.strip().strip('"').strip("'")
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8-sig") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def _credentials_path_env_nonempty() -> bool:
    """사용자가 파일 경로 방식을 쓰려는지(.env 또는 OS 환경변수)."""
    _hydrate_export_secrets()
    path_gs = (os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH") or "").strip()
    path_gac = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    return bool(path_gs or path_gac)


def _load_google_credentials_dict() -> dict[str, Any] | None:
    """서비스 계정 JSON. 파일 경로 우선; 경로가 비어 있지 않으면 인라인 JSON·B64는 시도하지 않음."""

    _hydrate_export_secrets()

    from_file = _load_credentials_from_path_env()
    if from_file:
        return from_file

    # OS 에 남은 깨진 GOOGLE_SHEETS_CREDENTIALS_JSON 과 충돌 방지:
    # PATH(또는 GOOGLE_APPLICATION_CREDENTIALS) 가 비어 있지 않으면 "파일만" 쓰는 것으로 간주.
    if _credentials_path_env_nonempty():
        return None

    b64 = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON_B64")
    if b64 and b64.strip():
        try:
            decoded = base64.standard_b64decode(b64.strip()).decode("utf-8")
            data = json.loads(decoded)
            if isinstance(data, dict):
                return data
        except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError, ValueError):
            pass

    raw_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if raw_json and raw_json.strip():
        r = raw_json.strip().strip('"').strip("'")
        if os.path.isfile(r):
            try:
                with open(r, encoding="utf-8-sig") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        parsed = _parse_credentials_json_string(raw_json)
        if parsed:
            return parsed

    return None


def sheets_skip_reason() -> str:
    """Sheets 가 비활성일 때 사용자에게 보여 줄 원인(비밀 미포함)."""
    _hydrate_export_secrets()
    sid = get_spreadsheet_id()
    if not sid:
        return (
            "GOOGLE_SHEETS_SPREADSHEET_ID 가 비어 있거나 잘못되었습니다. "
            "스프레드시트 URL 전체를 넣어도 됩니다."
        )
    creds = _load_google_credentials_dict()
    if creds:
        return "설정됨"

    hints: list[str] = []

    path_gs = (os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH") or "").strip()
    path_gac = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    chosen = path_gs or path_gac
    prefer_path_only = bool(chosen)

    if chosen:
        p = chosen.strip().strip('"').strip("'")
        if not os.path.isfile(p):
            hints.append(f"자격증명 파일 없음: {p}")
        else:
            hints.append(f"자격증명 파일은 있으나 JSON 오류: {p}")

    raw_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if raw_json and raw_json.strip() and not prefer_path_only:
        hints.append(
            "GOOGLE_SHEETS_CREDENTIALS_JSON 파싱 실패 — 가능하면 해당 변수를 비우고 "
            "GOOGLE_SHEETS_CREDENTIALS_PATH 에 서비스 계정 JSON 파일 경로만 두세요."
        )

    b64e = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON_B64")
    if b64e and b64e.strip() and not prefer_path_only:
        hints.append(
            "GOOGLE_SHEETS_CREDENTIALS_JSON_B64 디코딩·파싱 실패. 표준 Base64(줄바꿈 없음)인지 확인하세요."
        )

    if prefer_path_only and raw_json and raw_json.strip():
        hints.append(
            "(참고) Windows 등 OS 환경변수에 오래된 GOOGLE_SHEETS_CREDENTIALS_JSON 이 남아 있을 수 있습니다. "
            "경로 방식만 쓸 경우 해당 사용자/시스템 변수를 삭제하거나, `.env`에 빈 줄 "
            "`GOOGLE_SHEETS_CREDENTIALS_JSON=` 로 덮어쓰세요."
        )

    if hints:
        return " ".join(hints)

    return (
        "서비스 계정 자격증명 없음. 아래 중 하나를 설정하세요: "
        "GOOGLE_SHEETS_CREDENTIALS_PATH, GOOGLE_APPLICATION_CREDENTIALS, "
        "GOOGLE_SHEETS_CREDENTIALS_JSON, GOOGLE_SHEETS_CREDENTIALS_JSON_B64"
    )


def export_availability() -> dict[str, Any]:
    """UI용: 어떤 저장소가 설정됐는지."""
    _hydrate_export_secrets()
    return {
        "notion": bool(get_notion_token() and get_notion_database_id()),
        "sheets": bool(get_spreadsheet_id() and _load_google_credentials_dict()),
    }


def append_to_notion(
    *,
    page_label: str,
    title: str,
    question_snippet: str,
    summary_answer: str,
    session_id: str,
    model_name: str,
    started_at: datetime | None = None,
) -> None:
    """Notion 데이터베이스에 페이지 한 건 추가."""
    token = get_notion_token()
    db_id = get_notion_database_id()
    if not token or not db_id:
        raise RuntimeError("Notion이 설정되지 않았습니다. NOTION_TOKEN, NOTION_DATABASE_ID를 확인하세요.")
    if page_label not in NOTION_PAGE_OPTIONS:
        raise ValueError(f"페이지 라벨이 허용 목록에 없습니다: {page_label}")

    from notion_client import Client

    dt = started_at or datetime.now(timezone.utc)
    notion_dt = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    client = Client(auth=token)
    props: dict[str, Any] = {
        NOTION_PROP_NAME: {"title": [{"type": "text", "text": {"content": title[:2000]}}]},
        NOTION_PROP_PAGE: {"select": {"name": page_label}},
        NOTION_PROP_QUESTION: _rich_text_prop(question_snippet),
        NOTION_PROP_SUMMARY: _rich_text_prop(summary_answer),
        NOTION_PROP_DATETIME: {"date": {"start": notion_dt}},
        NOTION_PROP_SESSION: _rich_text_prop(session_id),
        NOTION_PROP_MODEL: _rich_text_prop(model_name),
    }
    client.pages.create(parent={"database_id": db_id.replace("-", "")}, properties=props)


def _split_cell(text: str, limit: int = _MAX_SHEET_CELL) -> list[str]:
    t = text or ""
    if not t:
        return []
    return [t[i : i + limit] for i in range(0, len(t), limit)]


def append_to_google_sheet(
    *,
    session_id: str,
    page_code: str,
    model_name: str,
    temperature: float,
    input_full: str,
    output_full: str,
    created_at: datetime | None = None,
) -> None:
    """스프레드시트에 행 추가. 셀 초과 시 같은 session_id로 여러 행(part)."""
    creds_dict = _load_google_credentials_dict()
    sid = get_spreadsheet_id()
    if not creds_dict or not sid:
        raise RuntimeError(
            "Google Sheets가 설정되지 않았습니다. GOOGLE_SHEETS_SPREADSHEET_ID와 "
            "서비스 계정 JSON(GOOGLE_SHEETS_CREDENTIALS_JSON 또는 PATH)을 확인하세요."
        )

    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sid)
    ws = sh.sheet1

    ts = created_at or datetime.now(timezone.utc)
    created_iso = ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    temp_s = str(temperature)

    in_parts = _split_cell(input_full) or [""]
    out_parts = _split_cell(output_full) or [""]
    n = max(len(in_parts), len(out_parts), 1)
    in_parts += [""] * (n - len(in_parts))
    out_parts += [""] * (n - len(out_parts))

    rows: list[list[Any]] = []
    for i in range(n):
        rows.append(
            [
                session_id,
                created_iso,
                page_code,
                model_name,
                temp_s,
                str(i),
                in_parts[i],
                out_parts[i],
            ]
        )

    for row in rows:
        ws.append_row(row, value_input_option="USER_ENTERED")


def new_session_id() -> str:
    return str(uuid.uuid4())


def log_estate_session(
    *,
    session_id: str,
    property_text: str,
    out1: str,
    out2: str,
    out3: str,
    summary: str,
    model_name: str,
    temperature: float,
) -> str:
    """부동산 심의 결과 기록."""
    av = export_availability()
    if not av["notion"] and not av["sheets"]:
        return "Notion·Sheets가 모두 설정되지 않았습니다. `.env` 또는 Secrets를 확인하세요."

    q_short = truncate_question_for_notion(property_text)
    title = f"[부동산] {q_short[:60]}" + ("…" if len(q_short) > 60 else "")
    full_in = f"【물건 정보】\n{property_text.strip()}"
    full_out = (
        f"【시장분석가】\n{out1}\n\n【비관론자】\n{out2}\n\n【세무/재무】\n{out3}\n\n【종합】\n{summary}"
    )
    now = datetime.now(timezone.utc)
    parts: list[str] = []

    if av["notion"]:
        try:
            append_to_notion(
                page_label="1 부동산",
                title=title,
                question_snippet=q_short,
                summary_answer=summary.strip(),
                session_id=session_id,
                model_name=model_name,
                started_at=now,
            )
            parts.append("Notion ✓")
        except Exception as e:
            parts.append(f"Notion 오류: {e}")
    else:
        parts.append("Notion 건너뜀(미설정)")

    if av["sheets"]:
        try:
            append_to_google_sheet(
                session_id=session_id,
                page_code="1_estate",
                model_name=model_name,
                temperature=temperature,
                input_full=full_in,
                output_full=full_out,
                created_at=now,
            )
            parts.append("Sheets ✓")
        except Exception as e:
            parts.append(f"Sheets 오류: {e}")
    else:
        parts.append(f"Sheets 건너뜀 — {sheets_skip_reason()}")

    return " ".join(parts)


def log_article_session(
    *,
    session_id: str,
    source_url: str,
    article_body: str,
    lab1: str,
    lab2: str,
    lab3: str,
    o1: str,
    o2: str,
    o3: str,
    summary: str,
    model_name: str,
    temperature: float,
    page_label: str,
    page_code: str,
    title_prefix: str,
) -> str:
    """기사 논평(철학/일반) 결과 기록."""
    av = export_availability()
    if not av["notion"] and not av["sheets"]:
        return "Notion·Sheets가 모두 설정되지 않았습니다. `.env` 또는 Secrets를 확인하세요."

    q_src = f"URL: {source_url}\n\n본문:\n{article_body.strip()}"
    q_short = truncate_question_for_notion(q_src)
    title = f"{title_prefix} {q_short[:50]}" + ("…" if len(q_short) > 50 else "")

    full_in = (
        f"【출처 URL】\n{source_url}\n\n【본문】\n{article_body.strip()}\n\n"
        f"【조언자】\n{lab1} / {lab2} / {lab3}"
    )
    full_out = (
        f"【{lab1}】\n{o1}\n\n【{lab2}】\n{o2}\n\n【{lab3}】\n{o3}\n\n【종합 메모】\n{summary}"
    )
    now = datetime.now(timezone.utc)
    parts: list[str] = []

    if av["notion"]:
        try:
            append_to_notion(
                page_label=page_label,
                title=title[:2000],
                question_snippet=q_short,
                summary_answer=summary.strip(),
                session_id=session_id,
                model_name=model_name,
                started_at=now,
            )
            parts.append("Notion ✓")
        except Exception as e:
            parts.append(f"Notion 오류: {e}")
    else:
        parts.append("Notion 건너뜀(미설정)")

    if av["sheets"]:
        try:
            append_to_google_sheet(
                session_id=session_id,
                page_code=page_code,
                model_name=model_name,
                temperature=temperature,
                input_full=full_in,
                output_full=full_out,
                created_at=now,
            )
            parts.append("Sheets ✓")
        except Exception as e:
            parts.append(f"Sheets 오류: {e}")
    else:
        parts.append(f"Sheets 건너뜀 — {sheets_skip_reason()}")

    return " ".join(parts)


def log_youtube_session(
    *,
    session_id: str,
    youtube_url: str,
    transcript_full: str,
    summary: str,
    model_name: str,
    temperature: float,
) -> str:
    av = export_availability()
    if not av["notion"] and not av["sheets"]:
        return "Notion·Sheets가 모두 설정되지 않았습니다. `.env` 또는 Secrets를 확인하세요."

    q_short = truncate_question_for_notion(youtube_url.strip(), max_len=2000)
    title = f"[유튜브] {q_short[:80]}" + ("…" if len(q_short) > 80 else "")
    full_in = f"【URL】\n{youtube_url.strip()}\n\n【자막 전체】\n{transcript_full}"
    full_out = f"【요약】\n{summary}"
    now = datetime.now(timezone.utc)
    parts: list[str] = []

    if av["notion"]:
        try:
            append_to_notion(
                page_label="4 유튜브",
                title=title,
                question_snippet=q_short,
                summary_answer=summary.strip(),
                session_id=session_id,
                model_name=model_name,
                started_at=now,
            )
            parts.append("Notion ✓")
        except Exception as e:
            parts.append(f"Notion 오류: {e}")
    else:
        parts.append("Notion 건너뜀(미설정)")

    if av["sheets"]:
        try:
            append_to_google_sheet(
                session_id=session_id,
                page_code="4_youtube",
                model_name=model_name,
                temperature=temperature,
                input_full=full_in,
                output_full=full_out,
                created_at=now,
            )
            parts.append("Sheets ✓")
        except Exception as e:
            parts.append(f"Sheets 오류: {e}")
    else:
        parts.append(f"Sheets 건너뜀 — {sheets_skip_reason()}")

    return " ".join(parts)
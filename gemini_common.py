# -*- coding: utf-8 -*-
"""Gemini API 키(.env + Streamlit Secrets), 공통 모델 설정 UI."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

GEMINI_MODEL_OPTIONS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


def _hydrate_secrets_from_streamlit() -> None:
    try:
        import streamlit as st

        sec = st.secrets
        for key in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            if key in sec and str(sec[key]).strip():
                os.environ.setdefault(key, str(sec[key]).strip())
    except Exception:
        pass


def get_gemini_api_key() -> str | None:
    _hydrate_secrets_from_streamlit()
    for env_name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        key = os.getenv(env_name)
        if key and key.strip():
            return key.strip()
    return None


def make_llm(model_name: str, temperature: float, api_key: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key,
    )


def api_key_missing_markdown() -> str:
    return (
        "**Google Gemini API 키가 설정되어 있지 않습니다.**\n\n"
        "**로컬:** `.env`에 `GOOGLE_API_KEY=...` 또는 `GEMINI_API_KEY=...`\n\n"
        "**Streamlit Cloud:** 앱 **Secrets**에 예시처럼 추가 후 재배포합니다.\n"
        "```toml\nGOOGLE_API_KEY = \"여기에_키\"\n```\n\n"
        "발급: [Google AI Studio](https://aistudio.google.com/apikey)"
    )


def render_sidebar_llm_settings(*, default_temperature: float = 0.5) -> tuple[str, float]:
    """각 페이지에서 동일한 사이드바 모델·온도 UI를 씁니다."""
    import streamlit as st

    with st.sidebar:
        st.markdown("### ⚙️ 모델 설정")
        model_name = st.selectbox(
            "Gemini 모델",
            options=GEMINI_MODEL_OPTIONS,
            index=0,
            help="계정에 따라 일부 모델만 허용될 수 있습니다.",
        )
        temperature = st.slider(
            "창의성(온도)",
            min_value=0.0,
            max_value=1.0,
            value=default_temperature,
            step=0.1,
        )
        st.divider()
        st.caption("좌측 상단 메뉴에서 다른 기능으로 이동할 수 있습니다.")
    return model_name, temperature


def streamlit_gemini_error_hints(err_lower: str) -> None:
    import streamlit as st

    el = err_lower.lower()
    if "api key" in el or "invalid" in el or "401" in el or "403" in el:
        st.warning("API 키·모델 권한을 확인하세요. Cloud에서는 Secrets와 재배포가 필요할 수 있습니다.")
    elif "429" in el or "quota" in el or "resource exhausted" in el:
        st.warning("요청 한도에 걸렸을 수 있습니다. 잠시 후 다시 시도하세요.")
    elif "404" in el or "not found" in el:
        st.warning("모델 ID를 찾지 못했습니다. 다른 모델을 선택해 보세요.")

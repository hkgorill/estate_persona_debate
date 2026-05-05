# -*- coding: utf-8 -*-
"""1. 부동산 가상 투자 심의 위원회 (Streamlit 페이지)."""

from __future__ import annotations

import traceback

import streamlit as st

from debate_estate import (
    SYSTEM_PROMPT_MARKET_ANALYST,
    SYSTEM_PROMPT_SKEPTIC,
    SYSTEM_PROMPT_TAX_FINANCE,
    build_estate_agent_chain,
    build_estate_summary_chain,
)
from gemini_common import (
    api_key_missing_markdown,
    get_gemini_api_key,
    render_sidebar_llm_settings,
    streamlit_gemini_error_hints,
)
from session_export import export_availability, log_estate_session, new_session_id

st.set_page_config(page_title="1. 부동산 심의", page_icon="🏛️", layout="wide")

st.title("🏛️ 1. 부동산 가상 투자 심의 위원회")
st.caption(
    "가상 에이전트 3인이 순차적으로 발언한 뒤, 종합 의견을 제시합니다. "
    "참고용 시뮬레이션이며 법률·세무·투자 자문이 아닙니다."
)

_av = export_availability()
if _av["notion"] or _av["sheets"]:
    st.caption(
        "기록: Notion·Sheets 환경이 감지되었습니다. 실행 후 **Notion·Google Sheets에 기록** 버튼으로 저장할 수 있습니다."
    )

model_name, temperature = render_sidebar_llm_settings(default_temperature=0.5)

if "p1_estate_log" not in st.session_state:
    st.session_state.p1_estate_log = None

property_text = st.text_area(
    "부동산 주소 또는 물건 정보",
    placeholder="예: 서울시 강남구 역삼동 지산 (또는 면적, 용도, 가격대 등)",
    height=120,
)

start = st.button("심의 시작", type="primary")

if start:
    if not property_text.strip():
        st.warning("물건 정보가 비어 있습니다.")
        st.session_state.p1_estate_log = None
    else:
        api_key = get_gemini_api_key()
        if not api_key:
            st.error(api_key_missing_markdown())
            st.session_state.p1_estate_log = None
        else:
            try:
                run_market = build_estate_agent_chain(
                    SYSTEM_PROMPT_MARKET_ANALYST, model_name, temperature, api_key
                )
                run_skeptic = build_estate_agent_chain(
                    SYSTEM_PROMPT_SKEPTIC, model_name, temperature, api_key
                )
                run_tax = build_estate_agent_chain(
                    SYSTEM_PROMPT_TAX_FINANCE, model_name, temperature, api_key
                )
                run_summary = build_estate_summary_chain(model_name, temperature, api_key)
            except Exception as e:
                st.error("LangChain / Gemini 초기화 오류")
                st.code(traceback.format_exc())
                st.caption(str(e))
                st.session_state.p1_estate_log = None
            else:
                prop = property_text.strip()
                try:
                    with st.spinner("에이전트 1 (시장분석가 📈) …"):
                        out1 = run_market(prop)
                    with st.spinner("에이전트 2 (비관론자 ⚠️) …"):
                        out2 = run_skeptic(prop)
                    with st.spinner("에이전트 3 (세무/재무 💰) …"):
                        out3 = run_tax(prop)
                    with st.spinner("의장 종합 요약 …"):
                        summary = run_summary(prop, out1, out2, out3)
                    st.session_state.p1_estate_log = {
                        "session_id": new_session_id(),
                        "property_text": prop,
                        "out1": out1,
                        "out2": out2,
                        "out3": out3,
                        "summary": summary,
                        "model_name": model_name,
                        "temperature": temperature,
                    }
                except Exception:
                    st.error("심의 진행 중 오류가 발생했습니다.")
                    tb = traceback.format_exc()
                    streamlit_gemini_error_hints(tb)
                    with st.expander("기술 상세"):
                        st.code(tb)
                    st.session_state.p1_estate_log = None

log_data = st.session_state.p1_estate_log

if not log_data:
    st.info("물건 정보를 입력한 뒤 **심의 시작**을 눌러 주세요.")
    st.stop()

st.divider()
st.subheader("심의 진행")

st.markdown("### 에이전트 1 — 시장분석가 📈")
st.write(log_data["out1"])
st.markdown("### 에이전트 2 — 비관론자 ⚠️")
st.write(log_data["out2"])
st.markdown("### 에이전트 3 — 세무/재무 전문가 💰")
st.write(log_data["out3"])
st.divider()
st.markdown("### 종합 투자 의견 및 핵심 고려사항")
st.success(log_data["summary"])

if _av["notion"] or _av["sheets"]:
    if st.button("Notion·Google Sheets에 기록", type="secondary", key="p1_export_btn"):
        msg = log_estate_session(
            session_id=log_data["session_id"],
            property_text=log_data["property_text"],
            out1=log_data["out1"],
            out2=log_data["out2"],
            out3=log_data["out3"],
            summary=log_data["summary"],
            model_name=log_data["model_name"],
            temperature=log_data["temperature"],
        )
        if "오류" in msg:
            st.warning(msg)
        else:
            st.success(msg)

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

st.set_page_config(page_title="1. 부동산 심의", page_icon="🏛️", layout="wide")

st.title("🏛️ 1. 부동산 가상 투자 심의 위원회")
st.caption(
    "가상 에이전트 3인이 순차적으로 발언한 뒤, 종합 의견을 제시합니다. "
    "참고용 시뮬레이션이며 법률·세무·투자 자문이 아닙니다."
)

model_name, temperature = render_sidebar_llm_settings(default_temperature=0.5)

property_text = st.text_area(
    "부동산 주소 또는 물건 정보",
    placeholder="예: 서울시 강남구 역삼동 지산 (또는 면적, 용도, 가격대 등)",
    height=120,
)

start = st.button("심의 시작", type="primary")

if not start:
    st.info("물건 정보를 입력한 뒤 **심의 시작**을 눌러 주세요.")
    st.stop()

if not property_text.strip():
    st.warning("물건 정보가 비어 있습니다.")
    st.stop()

api_key = get_gemini_api_key()
if not api_key:
    st.error(api_key_missing_markdown())
    st.stop()

try:
    run_market = build_estate_agent_chain(SYSTEM_PROMPT_MARKET_ANALYST, model_name, temperature, api_key)
    run_skeptic = build_estate_agent_chain(SYSTEM_PROMPT_SKEPTIC, model_name, temperature, api_key)
    run_tax = build_estate_agent_chain(SYSTEM_PROMPT_TAX_FINANCE, model_name, temperature, api_key)
    run_summary = build_estate_summary_chain(model_name, temperature, api_key)
except Exception as e:
    st.error("LangChain / Gemini 초기화 오류")
    st.code(traceback.format_exc())
    st.caption(str(e))
    st.stop()

prop = property_text.strip()
st.divider()
st.subheader("심의 진행")

try:
    with st.spinner("에이전트 1 (시장분석가 📈) …"):
        out1 = run_market(prop)
    st.markdown("### 에이전트 1 — 시장분석가 📈")
    st.write(out1)

    with st.spinner("에이전트 2 (비관론자 ⚠️) …"):
        out2 = run_skeptic(prop)
    st.markdown("### 에이전트 2 — 비관론자 ⚠️")
    st.write(out2)

    with st.spinner("에이전트 3 (세무/재무 💰) …"):
        out3 = run_tax(prop)
    st.markdown("### 에이전트 3 — 세무/재무 전문가 💰")
    st.write(out3)

    with st.spinner("의장 종합 요약 …"):
        summary = run_summary(prop, out1, out2, out3)

    st.divider()
    st.markdown("### 종합 투자 의견 및 핵심 고려사항")
    st.success(summary)

except Exception:
    st.error("심의 진행 중 오류가 발생했습니다.")
    tb = traceback.format_exc()
    streamlit_gemini_error_hints(tb)
    with st.expander("기술 상세"):
        st.code(tb)

# -*- coding: utf-8 -*-
"""1. 부동산 가상 투자 심의 위원회 (Streamlit 페이지)."""

from __future__ import annotations

import traceback

import streamlit as st

from debate_estate import build_estate_unified_chain
from gemini_common import (
    api_key_missing_markdown,
    get_gemini_api_key,
    render_sidebar_llm_settings,
    streamlit_gemini_error_hints,
)
from llm_usage import (
    USAGE_NOTE,
    format_usage_caption,
    merge_usage_totals,
    new_usage_handler,
    usage_invoke_config,
)
from session_export import export_availability, log_estate_session, new_session_id

st.set_page_config(page_title="1. 부동산 심의", page_icon="🏛️", layout="wide")

st.title("🏛️ 1. 부동산 가상 투자 심의 위원회")
st.caption(
    "가상 에이전트 3인과 의장 종합을 **한 번의 모델 호출**로 생성합니다(물건 정보 반복 전송을 줄여 토큰을 절감). "
    "참고용 시뮬레이션이며 법률·세무·투자 자문이 아닙니다."
)

_av = export_availability()
if _av["notion"] or _av["sheets"]:
    st.caption(
        "기록: Notion·Sheets가 설정된 경우, 실행이 끝나면 **자동으로** 저장합니다."
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
                run_unified = build_estate_unified_chain(model_name, temperature, api_key)
            except Exception as e:
                st.error("LangChain / Gemini 초기화 오류")
                st.code(traceback.format_exc())
                st.caption(str(e))
                st.session_state.p1_estate_log = None
            else:
                prop = property_text.strip()
                try:
                    usage_cb = new_usage_handler()
                    cfg = usage_invoke_config(usage_cb)
                    with st.spinner("위원 3인·의장 통합 생성 중…"):
                        out1, out2, out3, summary = run_unified(prop, config=cfg)
                    usage_totals = merge_usage_totals(usage_cb)
                    sid = new_session_id()
                    export_notice = None
                    if _av["notion"] or _av["sheets"]:
                        with st.spinner("Notion·Google Sheets 기록 중…"):
                            export_notice = log_estate_session(
                                session_id=sid,
                                property_text=prop,
                                out1=out1,
                                out2=out2,
                                out3=out3,
                                summary=summary,
                                model_name=model_name,
                                temperature=temperature,
                                usage_totals=usage_totals,
                            )
                    st.session_state.p1_estate_log = {
                        "session_id": sid,
                        "property_text": prop,
                        "out1": out1,
                        "out2": out2,
                        "out3": out3,
                        "summary": summary,
                        "model_name": model_name,
                        "temperature": temperature,
                        "usage_totals": usage_totals,
                        "export_notice": export_notice,
                    }
                except ValueError as e:
                    st.error(
                        "모델 응답 형식 오류입니다. 구간 태그(###MARKET### 등)가 빠졌거나 순서가 어긋났을 수 있습니다. "
                        "**심의 시작**을 다시 눌러 주세요."
                    )
                    st.caption(str(e))
                    st.session_state.p1_estate_log = None
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

_notice = log_data.get("export_notice")
if _notice:
    if "오류" in _notice:
        st.warning(_notice)
    else:
        st.success(_notice)

st.markdown("### 에이전트 1 — 시장분석가 📈")
st.write(log_data["out1"])
st.markdown("### 에이전트 2 — 비관론자 ⚠️")
st.write(log_data["out2"])
st.markdown("### 에이전트 3 — 세무/재무 전문가 💰")
st.write(log_data["out3"])
st.divider()
st.markdown("### 종합 투자 의견 및 핵심 고려사항")
st.success(log_data["summary"])

st.caption(format_usage_caption(log_data.get("usage_totals") or {}))
with st.expander("토큰 수 안내"):
    st.caption(USAGE_NOTE)

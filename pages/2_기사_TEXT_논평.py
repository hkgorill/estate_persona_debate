# -*- coding: utf-8 -*-
"""2. 시대의 현인 페르소나 기사 논평 (Streamlit 페이지)."""

from __future__ import annotations

import traceback

import streamlit as st

from article_sages import (
    SYSTEM_PROMPT_MENCIUS,
    SYSTEM_PROMPT_SCHOPENHAUER,
    SYSTEM_PROMPT_XUNZI,
    build_sage_comment_chain,
    build_sage_moderator_chain,
)
from gemini_common import (
    api_key_missing_markdown,
    get_gemini_api_key,
    render_sidebar_llm_settings,
    streamlit_gemini_error_hints,
)

st.set_page_config(page_title="2. 기사 TEXT 논평", page_icon="📜", layout="wide")

st.title("📜 2. 기사 TEXT 논평 (시대의 현인)")
st.caption(
    "맹자·순자·쇼펜하우어 페르소나가 순차 논평합니다. 역할 연기이며 실제 인물의 발언이 아닙니다. "
    "본문은 **직접 붙여 넣어** 주세요. URL은 자동 수집하지 않고 출처 문자열만 전달합니다."
)

model_name, temperature = render_sidebar_llm_settings(default_temperature=0.6)

source_url = st.text_input(
    "기사 링크 (선택)",
    placeholder="https://... (출처 표시용)",
)
article_body = st.text_area(
    "기사 본문 또는 논평할 텍스트 (필수)",
    placeholder="기사 전문 또는 주요 단락을 붙여 넣으세요.",
    height=220,
)

if st.button("논평 시작", type="primary"):
    if not article_body.strip():
        st.warning("본문이 비어 있습니다.")
        st.stop()

    api_key = get_gemini_api_key()
    if not api_key:
        st.error(api_key_missing_markdown())
        st.stop()

    url_disp = source_url.strip() if source_url else "(없음)"
    body = article_body.strip()

    try:
        run_m = build_sage_comment_chain(SYSTEM_PROMPT_MENCIUS, model_name, temperature, api_key)
        run_x = build_sage_comment_chain(SYSTEM_PROMPT_XUNZI, model_name, temperature, api_key)
        run_s = build_sage_comment_chain(SYSTEM_PROMPT_SCHOPENHAUER, model_name, temperature, api_key)
        run_mod = build_sage_moderator_chain(model_name, temperature, api_key)
    except Exception as e:
        st.error("모델 초기화 오류")
        st.code(traceback.format_exc())
        st.caption(str(e))
        st.stop()

    st.divider()
    st.subheader("논평 진행")

    try:
        with st.spinner("맹자 📜 …"):
            o1 = run_m(url_disp, body)
        st.markdown("### 맹자 📜")
        st.write(o1)

        with st.spinner("순자 ⚖️ …"):
            o2 = run_x(url_disp, body)
        st.markdown("### 순자 ⚖️")
        st.write(o2)

        with st.spinner("쇼펜하우어 🌑 …"):
            o3 = run_s(url_disp, body)
        st.markdown("### 쇼펜하우어 🌑")
        st.write(o3)

        with st.spinner("사회자 종합 메모 …"):
            summary = run_mod(url_disp, body, o1, o2, o3)

        st.divider()
        st.markdown("### 종합 메모")
        st.success(summary)

    except Exception:
        st.error("호출 중 오류가 발생했습니다.")
        tb = traceback.format_exc()
        streamlit_gemini_error_hints(tb)
        with st.expander("기술 상세"):
            st.code(tb)

else:
    st.info("본문을 입력한 뒤 **논평 시작**을 눌러 주세요.")

# -*- coding: utf-8 -*-
"""3. 주식 기사 — 투자 석학 페르소나 3명 선택·기타 입력 가능."""

from __future__ import annotations

import traceback

import streamlit as st

from article_persona_chains import (
    build_article_comment_chain,
    build_freeform_moderator_chain,
)
from gemini_common import (
    api_key_missing_markdown,
    get_gemini_api_key,
    render_sidebar_llm_settings,
    streamlit_gemini_error_hints,
)
from persona_presets import (
    BODY_LABEL_STOCK,
    MODERATOR_INVESTMENT,
    OTHER_OPTION_LABEL,
    investor_option_names,
    resolve_investor,
)

st.set_page_config(page_title="3. 주식 기사 논평", page_icon="📈", layout="wide")

st.title("📈 3. 주식 기사 석학 논평")
st.caption(
    "**조언을 구할 석학 3명**을 고릅니다(각 10명 프리셋 + 기타). "
    "**투자 자문·매매 추천이 아닙니다.** 본문은 직접 붙여 넣어 주세요."
)

model_name, temperature = render_sidebar_llm_settings(default_temperature=0.55)

_opts = investor_option_names()

st.markdown("##### 조언자 선택")
c1, c2, c3 = st.columns(3)
with c1:
    sel1 = st.selectbox("조언자 1", options=_opts, index=0, key="inv_sel1")
with c2:
    sel2 = st.selectbox("조언자 2", options=_opts, index=1, key="inv_sel2")
with c3:
    sel3 = st.selectbox("조언자 3", options=_opts, index=2, key="inv_sel3")

_need_other = OTHER_OPTION_LABEL in (sel1, sel2, sel3)
if _need_other:
    st.markdown(
        f"**{OTHER_OPTION_LABEL}**를 고른 칸에만 역할·관점 설명을 적어 주세요."
    )
    oc1, oc2, oc3 = st.columns(3)
    with oc1:
        other1 = st.text_area("기타 지침 — 조언자 1", height=100, key="inv_other1", disabled=sel1 != OTHER_OPTION_LABEL)
        if sel1 != OTHER_OPTION_LABEL:
            other1 = ""
    with oc2:
        other2 = st.text_area("기타 지침 — 조언자 2", height=100, key="inv_other2", disabled=sel2 != OTHER_OPTION_LABEL)
        if sel2 != OTHER_OPTION_LABEL:
            other2 = ""
    with oc3:
        other3 = st.text_area("기타 지침 — 조언자 3", height=100, key="inv_other3", disabled=sel3 != OTHER_OPTION_LABEL)
        if sel3 != OTHER_OPTION_LABEL:
            other3 = ""
else:
    other1 = other2 = other3 = ""

source_url = st.text_input(
    "기사 링크 (선택)",
    placeholder="https://... (출처 표시용, 자동 수집 없음)",
)
article_body = st.text_area(
    "주식 관련 기사 본문 또는 텍스트 (필수)",
    placeholder="뉴스 전문 또는 요약할 단락을 붙여 넣으세요.",
    height=220,
)

if st.button("석학 논평 시작", type="primary"):
    if not article_body.strip():
        st.warning("본문이 비어 있습니다.")
        st.stop()

    try:
        p1, lab1 = resolve_investor(sel1, other1)
        p2, lab2 = resolve_investor(sel2, other2)
        p3, lab3 = resolve_investor(sel3, other3)
    except ValueError as e:
        st.warning(str(e))
        st.stop()

    api_key = get_gemini_api_key()
    if not api_key:
        st.error(api_key_missing_markdown())
        st.stop()

    url_disp = source_url.strip() if source_url else "(없음)"
    body = article_body.strip()

    try:
        run_1 = build_article_comment_chain(
            p1, model_name, temperature, api_key, body_field_label=BODY_LABEL_STOCK
        )
        run_2 = build_article_comment_chain(
            p2, model_name, temperature, api_key, body_field_label=BODY_LABEL_STOCK
        )
        run_3 = build_article_comment_chain(
            p3, model_name, temperature, api_key, body_field_label=BODY_LABEL_STOCK
        )
        run_mod = build_freeform_moderator_chain(MODERATOR_INVESTMENT, model_name, temperature, api_key)
    except Exception as e:
        st.error("모델 초기화 오류")
        st.code(traceback.format_exc())
        st.caption(str(e))
        st.stop()

    st.divider()
    st.subheader("석학 논평 진행")

    try:
        with st.spinner(f"{lab1} …"):
            o1 = run_1(url_disp, body)
        st.markdown(f"### {lab1}")
        st.write(o1)

        with st.spinner(f"{lab2} …"):
            o2 = run_2(url_disp, body)
        st.markdown(f"### {lab2}")
        st.write(o2)

        with st.spinner(f"{lab3} …"):
            o3 = run_3(url_disp, body)
        st.markdown(f"### {lab3}")
        st.write(o3)

        with st.spinner("사회자 종합 메모 …"):
            summary = run_mod(url_disp, body, lab1, o1, lab2, o2, lab3, o3)

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
    st.info("조언자를 선택하고 본문을 입력한 뒤 **석학 논평 시작**을 눌러 주세요.")

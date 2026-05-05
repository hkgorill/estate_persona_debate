# -*- coding: utf-8 -*-
"""3. 주식 기사 — 투자 석학 페르소나 3명 선택·기타 입력 가능."""

from __future__ import annotations

import traceback

import streamlit as st

from article_persona_chains import build_article_unified_chain
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
from llm_usage import (
    USAGE_NOTE,
    format_usage_caption,
    merge_usage_totals,
    new_usage_handler,
    usage_invoke_config,
)
from session_export import export_availability, log_article_session, new_session_id

st.set_page_config(page_title="3. 주식 기사 논평", page_icon="📈", layout="wide")

st.title("📈 3. 주식 기사 석학 논평")
st.caption(
    "**조언을 구할 석학 3명**을 고릅니다(각 10명 프리셋 + 기타). "
    "세 논평과 종합 메모는 **한 번의 모델 호출**로 생성합니다(본문 반복 전송 최소화). "
    "**투자 자문·매매 추천이 아닙니다.** 본문은 직접 붙여 넣어 주세요."
)

_av = export_availability()
if _av["notion"] or _av["sheets"]:
    st.caption(
        "기록: Notion·Sheets가 설정된 경우, 실행이 끝나면 **자동으로** 저장합니다."
    )

model_name, temperature = render_sidebar_llm_settings(default_temperature=0.55)

if "p3_stock_log" not in st.session_state:
    st.session_state.p3_stock_log = None

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

run_clicked = st.button("석학 논평 시작", type="primary")

if run_clicked:
    if not article_body.strip():
        st.warning("본문이 비어 있습니다.")
        st.session_state.p3_stock_log = None
    else:
        try:
            p1, lab1 = resolve_investor(sel1, other1)
            p2, lab2 = resolve_investor(sel2, other2)
            p3, lab3 = resolve_investor(sel3, other3)
        except ValueError as e:
            st.warning(str(e))
            st.session_state.p3_stock_log = None
        else:
            api_key = get_gemini_api_key()
            if not api_key:
                st.error(api_key_missing_markdown())
                st.session_state.p3_stock_log = None
            else:
                url_disp = source_url.strip() if source_url else "(없음)"
                body = article_body.strip()
                try:
                    run_uni = build_article_unified_chain(
                        (p1, p2, p3),
                        MODERATOR_INVESTMENT,
                        model_name,
                        temperature,
                        api_key,
                        body_field_label=BODY_LABEL_STOCK,
                        persona_labels=(lab1, lab2, lab3),
                    )
                except Exception as e:
                    st.error("모델 초기화 오류")
                    st.code(traceback.format_exc())
                    st.caption(str(e))
                    st.session_state.p3_stock_log = None
                else:
                    try:
                        usage_cb = new_usage_handler()
                        cfg = usage_invoke_config(usage_cb)
                        with st.spinner("석학 3인·종합 통합 생성 중…"):
                            o1, o2, o3, summary = run_uni(url_disp, body, config=cfg)
                        usage_totals = merge_usage_totals(usage_cb)
                        sid = new_session_id()
                        export_notice = None
                        if _av["notion"] or _av["sheets"]:
                            with st.spinner("Notion·Google Sheets 기록 중…"):
                                export_notice = log_article_session(
                                    session_id=sid,
                                    source_url=url_disp,
                                    article_body=body,
                                    lab1=lab1,
                                    lab2=lab2,
                                    lab3=lab3,
                                    o1=o1,
                                    o2=o2,
                                    o3=o3,
                                    summary=summary,
                                    model_name=model_name,
                                    temperature=temperature,
                                    page_label="3 주식",
                                    page_code="3_stock",
                                    title_prefix="[주식]",
                                    usage_totals=usage_totals,
                                )
                        st.session_state.p3_stock_log = {
                            "session_id": sid,
                            "source_url": url_disp,
                            "article_body": body,
                            "lab1": lab1,
                            "lab2": lab2,
                            "lab3": lab3,
                            "o1": o1,
                            "o2": o2,
                            "o3": o3,
                            "summary": summary,
                            "model_name": model_name,
                            "temperature": temperature,
                            "usage_totals": usage_totals,
                            "export_notice": export_notice,
                        }
                    except ValueError as e:
                        st.error(
                            "모델 응답 형식 오류입니다. 구간 태그(###P1### 등)가 빠졌을 수 있습니다. "
                            "**석학 논평 시작**을 다시 눌러 주세요."
                        )
                        st.caption(str(e))
                        st.session_state.p3_stock_log = None
                    except Exception:
                        st.error("호출 중 오류가 발생했습니다.")
                        tb = traceback.format_exc()
                        streamlit_gemini_error_hints(tb)
                        with st.expander("기술 상세"):
                            st.code(tb)
                        st.session_state.p3_stock_log = None

log_data = st.session_state.p3_stock_log

if not log_data:
    st.info("조언자를 선택하고 본문을 입력한 뒤 **석학 논평 시작**을 눌러 주세요.")
    st.stop()

st.divider()
st.subheader("석학 논평 진행")

_notice = log_data.get("export_notice")
if _notice:
    if "오류" in _notice:
        st.warning(_notice)
    else:
        st.success(_notice)

st.markdown(f"### {log_data['lab1']}")
st.write(log_data["o1"])
st.markdown(f"### {log_data['lab2']}")
st.write(log_data["o2"])
st.markdown(f"### {log_data['lab3']}")
st.write(log_data["o3"])
st.divider()
st.markdown("### 종합 메모")
st.success(log_data["summary"])

st.caption(format_usage_caption(log_data.get("usage_totals") or {}))
with st.expander("토큰 수 안내"):
    st.caption(USAGE_NOTE)

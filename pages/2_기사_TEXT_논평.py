# -*- coding: utf-8 -*-
"""2. 시대의 현인 페르소나 기사 논평 — 조언자 3명 선택·기타 입력 가능."""

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
    BODY_LABEL_GENERAL,
    MODERATOR_PHILOSOPHY,
    OTHER_OPTION_LABEL,
    philosophy_option_names,
    resolve_philosophy,
)
from llm_usage import (
    USAGE_NOTE,
    format_usage_caption,
    merge_usage_totals,
    new_usage_handler,
    usage_invoke_config,
)
from session_export import export_availability, log_article_session, new_session_id

st.set_page_config(page_title="2. 기사 TEXT 논평", page_icon="📜", layout="wide")

st.title("📜 2. 기사 TEXT 논평 (시대의 현인)")
st.caption(
    "아래에서 **조언을 구할 현인 3명**을 고릅니다. 목록에 없으면 **기타**를 선택하고 역할을 직접 적어 주세요. "
    "세 논평과 종합 메모는 **한 번의 모델 호출**로 생성합니다(본문 반복 전송 최소화). "
    "역할 연기이며 실제 인물의 발언이 아닙니다. 본문은 직접 붙여 넣어 주세요."
)

_av = export_availability()
if _av["notion"] or _av["sheets"]:
    st.caption(
        "기록: Notion·Sheets 환경이 감지되었습니다. 실행 후 **Notion·Google Sheets에 기록**으로 저장할 수 있습니다."
    )

model_name, temperature = render_sidebar_llm_settings(default_temperature=0.6)

if "p2_article_log" not in st.session_state:
    st.session_state.p2_article_log = None

_opts = philosophy_option_names()

st.markdown("##### 조언자 선택 (각 10명 프리셋 + 기타)")
c1, c2, c3 = st.columns(3)
with c1:
    sel1 = st.selectbox("조언자 1", options=_opts, index=0, key="ph_sel1")
with c2:
    sel2 = st.selectbox("조언자 2", options=_opts, index=1, key="ph_sel2")
with c3:
    sel3 = st.selectbox("조언자 3", options=_opts, index=2, key="ph_sel3")

_need_other = OTHER_OPTION_LABEL in (sel1, sel2, sel3)
if _need_other:
    st.markdown(
        f"**{OTHER_OPTION_LABEL}**를 고른 칸에만 해당하는 설명을 적어 주세요. (프리셋만 선택한 칸은 비워 두어도 됩니다.)"
    )
    oc1, oc2, oc3 = st.columns(3)
    with oc1:
        other1 = st.text_area("기타 지침 — 조언자 1", height=100, key="ph_other1", disabled=sel1 != OTHER_OPTION_LABEL)
        if sel1 != OTHER_OPTION_LABEL:
            other1 = ""
    with oc2:
        other2 = st.text_area("기타 지침 — 조언자 2", height=100, key="ph_other2", disabled=sel2 != OTHER_OPTION_LABEL)
        if sel2 != OTHER_OPTION_LABEL:
            other2 = ""
    with oc3:
        other3 = st.text_area("기타 지침 — 조언자 3", height=100, key="ph_other3", disabled=sel3 != OTHER_OPTION_LABEL)
        if sel3 != OTHER_OPTION_LABEL:
            other3 = ""
else:
    other1 = other2 = other3 = ""

source_url = st.text_input(
    "기사 링크 (선택)",
    placeholder="https://... (출처 표시용)",
)
article_body = st.text_area(
    "기사 본문 또는 논평할 텍스트 (필수)",
    placeholder="기사 전문 또는 주요 단락을 붙여 넣으세요.",
    height=220,
)

run_clicked = st.button("논평 시작", type="primary")

if run_clicked:
    if not article_body.strip():
        st.warning("본문이 비어 있습니다.")
        st.session_state.p2_article_log = None
    else:
        try:
            p1, lab1 = resolve_philosophy(sel1, other1)
            p2, lab2 = resolve_philosophy(sel2, other2)
            p3, lab3 = resolve_philosophy(sel3, other3)
        except ValueError as e:
            st.warning(str(e))
            st.session_state.p2_article_log = None
        else:
            api_key = get_gemini_api_key()
            if not api_key:
                st.error(api_key_missing_markdown())
                st.session_state.p2_article_log = None
            else:
                url_disp = source_url.strip() if source_url else "(없음)"
                body = article_body.strip()
                try:
                    run_uni = build_article_unified_chain(
                        (p1, p2, p3),
                        MODERATOR_PHILOSOPHY,
                        model_name,
                        temperature,
                        api_key,
                        body_field_label=BODY_LABEL_GENERAL,
                        persona_labels=(lab1, lab2, lab3),
                    )
                except Exception as e:
                    st.error("모델 초기화 오류")
                    st.code(traceback.format_exc())
                    st.caption(str(e))
                    st.session_state.p2_article_log = None
                else:
                    try:
                        usage_cb = new_usage_handler()
                        cfg = usage_invoke_config(usage_cb)
                        with st.spinner("조언자 3인·종합 통합 생성 중…"):
                            o1, o2, o3, summary = run_uni(url_disp, body, config=cfg)
                        usage_totals = merge_usage_totals(usage_cb)
                        st.session_state.p2_article_log = {
                            "session_id": new_session_id(),
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
                        }
                    except ValueError as e:
                        st.error(
                            "모델 응답 형식 오류입니다. 구간 태그(###P1### 등)가 빠졌을 수 있습니다. "
                            "**논평 시작**을 다시 눌러 주세요."
                        )
                        st.caption(str(e))
                        st.session_state.p2_article_log = None
                    except Exception:
                        st.error("호출 중 오류가 발생했습니다.")
                        tb = traceback.format_exc()
                        streamlit_gemini_error_hints(tb)
                        with st.expander("기술 상세"):
                            st.code(tb)
                        st.session_state.p2_article_log = None

log_data = st.session_state.p2_article_log

if not log_data:
    st.info("조언자를 선택하고 본문을 입력한 뒤 **논평 시작**을 눌러 주세요.")
    st.stop()

st.divider()
st.subheader("논평 진행")

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

if _av["notion"] or _av["sheets"]:
    if st.button("Notion·Google Sheets에 기록", type="secondary", key="p2_export_btn"):
        msg = log_article_session(
            session_id=log_data["session_id"],
            source_url=log_data["source_url"],
            article_body=log_data["article_body"],
            lab1=log_data["lab1"],
            lab2=log_data["lab2"],
            lab3=log_data["lab3"],
            o1=log_data["o1"],
            o2=log_data["o2"],
            o3=log_data["o3"],
            summary=log_data["summary"],
            model_name=log_data["model_name"],
            temperature=log_data["temperature"],
            page_label="2 기사",
            page_code="2_article",
            title_prefix="[기사]",
            usage_totals=log_data.get("usage_totals"),
        )
        if "오류" in msg:
            st.warning(msg)
        else:
            st.success(msg)

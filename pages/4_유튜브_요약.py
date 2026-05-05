# -*- coding: utf-8 -*-
"""4. 유튜브 요약 — URL 자막 기반 Gemini 요약."""

from __future__ import annotations

import traceback

import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from gemini_common import (
    api_key_missing_markdown,
    get_gemini_api_key,
    make_llm,
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
from session_export import export_availability, log_youtube_session, new_session_id
from youtube_transcript_api import YouTubeTranscriptApiException
from youtube_transcript_util import (
    extract_youtube_video_id,
    fetch_transcript_plain_text,
    user_message_for_transcript_error,
)

st.set_page_config(page_title="4. 유튜브 요약", page_icon="🎬", layout="wide")

st.title("🎬 4. 유튜브 요약")
st.caption(
    "유튜브 영상 **URL**을 넣으면 공개 자막을 불러와 **Gemini**로 내용을 요약합니다. "
    "자막이 없는 영상·연령 제한 등은 동작하지 않을 수 있습니다."
)

_av = export_availability()
if _av["notion"] or _av["sheets"]:
    st.caption(
        "기록: Notion·Sheets가 설정된 경우, 요약이 끝나면 **자동으로** 저장합니다."
    )

model_name, temperature = render_sidebar_llm_settings(default_temperature=0.3)

if "p4_youtube_log" not in st.session_state:
    st.session_state.p4_youtube_log = None

MAX_TRANSCRIPT_CHARS = 120_000

youtube_url = st.text_input(
    "유튜브 주소",
    placeholder="https://www.youtube.com/watch?v=... 또는 https://youtu.be/...",
)

run_clicked = st.button("자막 불러오기 후 요약", type="primary")

if run_clicked:
    vid = extract_youtube_video_id(youtube_url)
    if not vid:
        st.warning("인식할 수 있는 유튜브 주소가 아닙니다. watch·youtu.be·shorts·embed 형식을 확인해 주세요.")
        st.session_state.p4_youtube_log = None
    else:
        api_key = get_gemini_api_key()
        if not api_key:
            st.error(api_key_missing_markdown())
            st.session_state.p4_youtube_log = None
        else:
            try:
                with st.spinner("자막을 가져오는 중…"):
                    raw = fetch_transcript_plain_text(vid)
            except YouTubeTranscriptApiException as e:
                st.warning(user_message_for_transcript_error(e))
                st.session_state.p4_youtube_log = None
                raw = None
            except Exception:
                st.error("자막 수집 중 예기치 않은 오류")
                st.code(traceback.format_exc())
                st.session_state.p4_youtube_log = None
                raw = None

            if raw is not None:
                truncated = False
                transcript_for_llm = raw
                if len(transcript_for_llm) > MAX_TRANSCRIPT_CHARS:
                    transcript_for_llm = transcript_for_llm[:MAX_TRANSCRIPT_CHARS]
                    truncated = True

                if truncated:
                    st.info(f"자막이 길어 앞부분만 사용합니다. (최대 약 {MAX_TRANSCRIPT_CHARS:,}자)")

                system = (
                    "당신은 유튜브 영상의 **자막 텍스트만**을 근거로 내용을 정리합니다.\n"
                    "- 자막 인식 오류·반복·무의미한 구절은 건너뜁니다.\n"
                    "- 영상이 다루는 **주제**, **전개 순서**, **핵심 정보·주장**, **마무리**를 한국어로 구조적으로 요약합니다.\n"
                    "- 자막에 없는 사실은 추측하지 않습니다."
                )
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", system),
                        (
                            "human",
                            "【영상 URL】\n{url}\n\n【자막】\n{transcript}\n\n"
                            "위 자막만 바탕으로 요약해 주세요. 제목은 URL·자막에서 확실히 알 수 있을 때만 언급합니다.",
                        ),
                    ]
                )

                try:
                    llm = make_llm(model_name, temperature, api_key)
                    chain = prompt | llm | StrOutputParser()
                    usage_cb = new_usage_handler()
                    cfg = usage_invoke_config(usage_cb)
                    with st.spinner("요약 생성 중…"):
                        summary = chain.invoke(
                            {
                                "url": youtube_url.strip(),
                                "transcript": transcript_for_llm,
                            },
                            config=cfg,
                        )
                    usage_totals = merge_usage_totals(usage_cb)
                    sid = new_session_id()
                    export_notice = None
                    if _av["notion"] or _av["sheets"]:
                        with st.spinner("Notion·Google Sheets 기록 중…"):
                            export_notice = log_youtube_session(
                                session_id=sid,
                                youtube_url=youtube_url.strip(),
                                transcript_full=raw,
                                summary=summary,
                                model_name=model_name,
                                temperature=temperature,
                                usage_totals=usage_totals,
                            )
                    st.session_state.p4_youtube_log = {
                        "session_id": sid,
                        "youtube_url": youtube_url.strip(),
                        "transcript_full": raw,
                        "summary": summary,
                        "model_name": model_name,
                        "temperature": temperature,
                        "usage_totals": usage_totals,
                        "export_notice": export_notice,
                    }
                except Exception as e:
                    st.error("요약 생성 오류")
                    streamlit_gemini_error_hints(str(e))
                    st.code(traceback.format_exc())
                    st.caption(str(e))
                    st.session_state.p4_youtube_log = None

log_data = st.session_state.p4_youtube_log

if not log_data:
    st.divider()
    st.markdown(
        """
**향후 아이디어**
- 다른 페르소나 세트 (예: 과학자·작가·거시경제 학파)
- 요약 + 논평 파이프라인
- 사용자 정의 시스템 프롬프트 저장
"""
    )
    st.caption(
        "자막은 `youtube-transcript-api`로 가져오며, 요약은 `gemini_common`과 동일한 키·모델 패턴을 사용합니다."
    )
    st.stop()

st.divider()
st.subheader("요약")

_notice = log_data.get("export_notice")
if _notice:
    if "오류" in _notice:
        st.warning(_notice)
    else:
        st.success(_notice)

st.markdown(log_data["summary"])

st.caption(format_usage_caption(log_data.get("usage_totals") or {}))
with st.expander("토큰 수 안내"):
    st.caption(USAGE_NOTE)

with st.expander("참고: 사용한 자막 일부(미리보기)"):
    preview = log_data["transcript_full"][:8000] + (
        "…" if len(log_data["transcript_full"]) > 8000 else ""
    )
    st.text(preview)

st.divider()
st.markdown(
    """
**향후 아이디어**
- 다른 페르소나 세트 (예: 과학자·작가·거시경제 학파)
- 요약 + 논평 파이프라인
- 사용자 정의 시스템 프롬프트 저장
"""
)
st.caption(
    "자막은 `youtube-transcript-api`로 가져오며, 요약은 `gemini_common`과 동일한 키·모델 패턴을 사용합니다."
)

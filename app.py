# -*- coding: utf-8 -*-
"""
페르소나 멀티 에이전트 데모 — 홈(진입점).

실행: python -m streamlit run app.py

좌측 사이드바 상단의 페이지 목록에서 기능을 선택합니다.
  • 1 — 부동산 가상 투자 심의
  • 2 — 기사 TEXT 논평 (맹자·순자·쇼펜하우어)
  • 3 — 주식 기사 논평 (워렌 버핏·그레이엄·피터 린치)
  • 4 — 유튜브 요약 (자막 기반)
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="홈 | 페르소나 토론",
    page_icon="🏠",
    layout="wide",
)

st.title("🏠 페르소나 멀티 에이전트 데모")
st.markdown(
    """
환영합니다. **좌측 사이드바**(또는 모바일에서는 상단 메뉴)에서 아래 페이지를 선택해 주세요.

| 순서 | 페이지 | 설명 |
|:---:|:---|:---|
| **1** | **부동산 심의** | 물건 정보 입력 → 시장분석가·비관론자·세무/재무 위원 순차 발언 → 종합 의견 |
| **2** | **기사 TEXT 논평** | 조언자 3명: 철학 프리셋 10인 또는 **기타** 입력 → 순차 논평 → 종합 메모 |
| **3** | **주식 기사 논평** | 조언자 3명: 투자 프리셋 10인 또는 **기타** 입력 → 순차 논평 → 종합 메모 |
| **4** | **유튜브 요약** | URL 입력 → 공개 자막 수집 → **Gemini**로 내용 요약 |

---
"""
)

st.info(
    "각 기능 페이지의 **사이드바**에서 Gemini 모델과 온도를 바꿀 수 있습니다. "
    "API 키는 로컬 `.env` 또는 Streamlit Cloud **Secrets**의 `GOOGLE_API_KEY` 로 설정합니다."
)

with st.expander("개발자 참고"):
    st.markdown(
        "- 공통: `gemini_common.py` (키 로드, LLM 팩토리, 사이드바 모델 UI)\n"
        "- 부동산 로직: `debate_estate.py` (위원 3·의장 **통합 단일 호출**)\n"
        "- 기사/주식 논평 프리셋: `persona_presets.py`\n"
        "- 논평 LangChain 공통: `article_persona_chains.py` (조언자 3·사회자 **통합 단일 호출**)\n"
        "- UI: `app.py`(홈), `pages/1_*.py` ~ `4_*.py`"
    )

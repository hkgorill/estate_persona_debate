# -*- coding: utf-8 -*-
"""3. 추후 확장용 플레이스홀더 페이지."""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="3. 추후 확장", page_icon="🔜", layout="wide")

st.title("🔜 3. 추후 확장")
st.markdown(
    """
이 페이지는 **향후 기능**을 붙이기 위한 자리입니다.

예시 아이디어:
- 다른 페르소나 세트 (예: 과학자·작가·정치 이론가)
- 요약 + 논평 파이프라인
- 사용자 정의 시스템 프롬프트 저장
"""
)

st.info(
    "구현 시에는 `gemini_common.py`의 키·모델 유틸과 동일 패턴으로 "
    "`pages/` 또는 별도 도메인 모듈(예: `your_feature.py`)을 추가하면 됩니다."
)

# -*- coding: utf-8 -*-
"""
부동산 가상 투자 심의 위원회 — Streamlit 메인 앱 (Google Gemini API)

실행 방법 (터미널에서 프로젝트 폴더로 이동한 뒤):
    1) 가상환경 생성 및 활성화 (선택이지만 권장)
    2) pip install -r requirements.txt
    3) .env 파일에 GOOGLE_API_KEY (또는 GEMINI_API_KEY) 설정
    4) streamlit run app.py

※ 개발 서버는 사용자 환경에서 직접 실행해 주세요.
"""

from __future__ import annotations

import os
import traceback
from typing import Callable

import streamlit as st
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


# ---------------------------------------------------------------------------
# 1) 환경 변수 로드 (.env 파일의 GOOGLE_API_KEY / GEMINI_API_KEY 등)
#    - 프로젝트 루트의 .env 를 읽습니다.
#    - 이미 OS 환경변수로 설정되어 있으면 그 값이 우선될 수 있습니다.
# ---------------------------------------------------------------------------
load_dotenv()


# ---------------------------------------------------------------------------
# 2) 에이전트별 시스템 프롬프트 (역할이 명확히 분리되도록 상수로 관리)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_MARKET_ANALYST = """당신은 부동산 시장 분석가입니다. (페르소나: 시장분석가 📈)

사용자가 입력한 주소 또는 물건 설명만을 바탕으로, 일반적인 부동산 분석 프레임워크로 논의하세요.
실제 현장 조사나 최신 시세 데이터가 없다는 점을 명시하고, 가정과 한계를 분명히 밝히세요.

다음 관점을 중심으로 체계적으로 서술하세요:
- 입지(접근성, 생활 인프라 등 가정 가능한 요소)
- 호재·리스크로 해석될 수 있는 요소(일반론 수준)
- 주변 시세·시장 분위기(공개 데이터 없이 추정일 경우 추정임을 표시)
- 향후 가치 상승 여력에 대한 조건부 의견

한국어로, 전문적이지만 초보 투자자도 이해할 수 있게 작성하세요."""


SYSTEM_PROMPT_SKEPTIC = """당신은 부동산 투자에 대해 신중한 비관론자(악마의 변호인)입니다. (페르소나: 비관론자 ⚠️)

사용자 입력 정보만으로는 확정적 단정을 하지 말고, 가능한 최악의 시나리오와 반론을 제기하세요.

다음을 공격적으로(논리적으로) 점검하세요:
- 공실·임대 수요 둔화 리스크
- 금리·금융비용 변동이 현금흐름에 미칠 수 있는 압박
- 상권 쇠퇴·업종 변화·지역 경기 둔화 시나리오
- 유동성·매각 난이도 등 스트레스 상황

반드시 "이는 시나리오이며 실제는 다를 수 있다"는 점을 한 문장 이상으로 명시하세요.
한국어로 작성하세요."""


SYSTEM_PROMPT_TAX_FINANCE = """당신은 부동산 취득·보유·임대와 관련된 세무·재무를 다루는 전문가입니다. (페르소나: 세무/재무 전문가 💰)

구체 금액은 사용자가 제공하지 않는 한 임의로 단정하지 말고, 일반적인 세목·비용 항목과 계산 시 필요한 가정을 나열하세요.
법령·세율은 시점에 따라 변동될 수 있음을 명시하고, 최종 판단은 세무사 등 전문가 자문이 필요함을 안내하세요.

다음을 다루세요:
- 취득세·지방세·부대 비용 등 취득 단계 비용의 체크리스트
- 대출이자 부담을 점검할 때 필요한 가정(금리, LTV, 상환 방식)
- 임대 수익이 있다고 가정할 때의 현금흐름·간이 수익률 산출 틀
- 보유 기간·처분 시 고려할 요소(개략)

한국어로 작성하세요."""


SYSTEM_PROMPT_CHAIR_SUMMARY = """당신은 위원회의 의장입니다. 앞선 세 명의 발언(시장분석가, 비관론자, 세무/재무 전문가)을 모두 읽고,
투자자가 다음 단계에서 무엇을 확인해야 할지 중심으로 '종합 투자 의견 및 핵심 고려사항'을 요약하세요.

규칙:
- 새로운 사실을 지어내지 말고, 앞선 분석에서 나온 논점만 통합하세요.
- 균형 잡힌 결론(기회 vs 리스크)을 1~2문단으로 제시한 뒤, 핵심 고려사항을 bullet 형태로 5~8개 나열하세요.
- 투자 권유/비권유를 단정하지 말고, 조건부 의견으로 작성하세요.
한국어로 작성하세요."""


# ---------------------------------------------------------------------------
# 3) LangChain 체인 구성 (프롬프트 + Gemini + 문자열 파서)
# ---------------------------------------------------------------------------

def _make_llm(model_name: str, temperature: float, api_key: str) -> ChatGoogleGenerativeAI:
    """
    Google Generative AI(Gemini) 채팅 모델 인스턴스를 생성합니다.
    api_key는 .env에서 읽은 값을 명시적으로 넘깁니다(GOOGLE_API_KEY / GEMINI_API_KEY 호환).
    """
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key,
    )


def _build_chain(
    system_prompt: str,
    model_name: str,
    temperature: float,
    api_key: str,
) -> Callable[[str], str]:
    """
    동일한 패턴으로 에이전트 체인을 만듭니다.
    반환값: property_text 하나를 받아 최종 문자열을 돌려주는 호출 가능 객체.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "【심의 대상 물건 정보】\n{property_text}\n\n위 정보를 바탕으로 위원 역할에 맞게 분석·발언해 주세요.",
            ),
        ]
    )
    llm = _make_llm(model_name, temperature, api_key)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke


def _build_summary_chain(
    model_name: str,
    temperature: float,
    api_key: str,
) -> Callable[[str, str, str, str], str]:
    """세 에이전트 결과 + 원문 물건 정보를 넣어 종합 요약 체인을 만듭니다."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT_CHAIR_SUMMARY),
            (
                "human",
                "【원본 물건 정보】\n{property_text}\n\n"
                "【시장분석가 발언】\n{agent1}\n\n"
                "【비관론자 발언】\n{agent2}\n\n"
                "【세무/재무 전문가 발언】\n{agent3}\n\n"
                "위 내용을 바탕으로 종합 투자 의견 및 핵심 고려사항을 작성해 주세요.",
            ),
        ]
    )
    llm = _make_llm(model_name, temperature, api_key)
    chain = prompt | llm | StrOutputParser()

    def _invoke(property_text: str, a1: str, a2: str, a3: str) -> str:
        return chain.invoke(
            {"property_text": property_text, "agent1": a1, "agent2": a2, "agent3": a3}
        )

    return _invoke


def get_gemini_api_key() -> str | None:
    """
    Gemini( Google AI ) 호출에 사용할 API 키를 환경 변수에서 읽습니다.
    - LangChain 권장: GOOGLE_API_KEY
    - 호환: GEMINI_API_KEY (AI Studio에서 복사한 키를 이 이름으로 두는 경우가 많음)
    """
    for env_name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        key = os.getenv(env_name)
        if key and key.strip():
            return key.strip()
    return None


# ---------------------------------------------------------------------------
# 4) Streamlit UI
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="부동산 가상 투자 심의 위원회",
        page_icon="🏛️",
        layout="wide",
    )

    st.title("🏛️ 부동산 가상 투자 심의 위원회")
    st.caption(
        "가상 에이전트 3인이 순차적으로 발언한 뒤, 종합 의견을 제시합니다. "
        "본 서비스는 참고용 시뮬레이션이며 법률·세무·투자 자문이 아닙니다."
    )

    # 사이드바: 모델·온도 설정 (초보자도 조절 가능하도록 단순 노출)
    with st.sidebar:
        st.header("설정")
        model_name = st.selectbox(
            "Gemini 모델",
            options=[
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ],
            index=0,
            help="계정·지역에 따라 일부 모델만 허용될 수 있습니다. 오류 시 다른 모델을 선택해 보세요.",
        )
        temperature = st.slider("창의성(온도)", min_value=0.0, max_value=1.0, value=0.5, step=0.1)

    property_text = st.text_area(
        "부동산 주소 또는 물건 정보",
        placeholder="예: 서울시 강남구 역삼동 지산 (또는 면적, 용도, 가격대 등 알고 있는 정보)",
        height=120,
    )

    start = st.button("심의 시작", type="primary")

    if not start:
        st.info("물건 정보를 입력한 뒤 **심의 시작** 버튼을 눌러 주세요.")
        return

    if not property_text.strip():
        st.warning("물건 정보가 비어 있습니다. 주소나 물건 설명을 입력해 주세요.")
        return

    # API 키 검증
    api_key = get_gemini_api_key()
    if not api_key:
        st.error(
            "**Google Gemini API 키가 설정되어 있지 않습니다.**\n\n"
            "1. [Google AI Studio](https://aistudio.google.com/apikey)에서 API 키를 발급합니다.\n"
            "2. 프로젝트 폴더에 `.env` 파일을 만듭니다.\n"
            "3. 다음 중 **하나**를 넣습니다:\n"
            "   - `GOOGLE_API_KEY=...` (LangChain 기본 권장)\n"
            "   - 또는 `GEMINI_API_KEY=...`\n"
            "4. `.env.example` 파일을 참고해 주세요.\n\n"
            "이미 `.env`를 만들었다면, 파일 위치가 `app.py`와 같은 폴더인지 확인하고 "
            "에디터 저장 후 앱을 다시 실행해 보세요."
        )
        return

    # 체인 생성
    try:
        run_market = _build_chain(SYSTEM_PROMPT_MARKET_ANALYST, model_name, temperature, api_key)
        run_skeptic = _build_chain(SYSTEM_PROMPT_SKEPTIC, model_name, temperature, api_key)
        run_tax = _build_chain(SYSTEM_PROMPT_TAX_FINANCE, model_name, temperature, api_key)
        run_summary = _build_summary_chain(model_name, temperature, api_key)
    except Exception as e:
        st.error("LangChain / Gemini 클라이언트 초기화 중 오류가 발생했습니다.")
        st.code(traceback.format_exc())
        st.caption(f"요약 메시지: {e!s}")
        return

    prop = property_text.strip()

    st.divider()
    st.subheader("심의 진행")

    # 순차 실행 + 각 단계 예외 처리
    try:
        with st.spinner("에이전트 1 (시장분석가 📈) 발언 준비 중…"):
            out1 = run_market(prop)
        st.markdown("### 에이전트 1 — 시장분석가 📈")
        st.write(out1)

        with st.spinner("에이전트 2 (비관론자 ⚠️) 발언 준비 중…"):
            out2 = run_skeptic(prop)
        st.markdown("### 에이전트 2 — 비관론자 ⚠️")
        st.write(out2)

        with st.spinner("에이전트 3 (세무/재무 전문가 💰) 발언 준비 중…"):
            out3 = run_tax(prop)
        st.markdown("### 에이전트 3 — 세무/재무 전문가 💰")
        st.write(out3)

        with st.spinner("의장 종합 요약 작성 중…"):
            summary = run_summary(prop, out1, out2, out3)

        st.divider()
        st.markdown("### 종합 투자 의견 및 핵심 고려사항")
        st.success(summary)

    except Exception as e:
        err_text = str(e).lower()
        st.error("심의 진행 중 오류가 발생했습니다. 아래 내용을 확인해 주세요.")

        # Gemini / Google API 흔한 오류 안내
        if "api key" in err_text or "invalid" in err_text or "401" in err_text or "403" in err_text:
            st.warning(
                "API 키가 잘못되었거나, 해당 키에 모델 사용 권한이 없을 수 있습니다. "
                "`.env`의 `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY`를 확인하고, "
                "AI Studio에서 해당 모델이 활성화되어 있는지 확인하세요."
            )
        elif "429" in err_text or "quota" in err_text or "resource exhausted" in err_text:
            st.warning("요청 한도(쿼터)에 도달했을 수 있습니다. 잠시 후 다시 시도하거나 사용량 한도를 확인하세요.")
        elif "404" in err_text or "not found" in err_text:
            st.warning(
                "선택한 모델 이름을 API에서 찾지 못했습니다. "
                "사이드바에서 다른 Gemini 모델을 선택해 보세요."
            )

        with st.expander("기술 상세 (개발자용)"):
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()

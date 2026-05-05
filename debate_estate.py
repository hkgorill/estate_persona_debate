# -*- coding: utf-8 -*-
"""부동산 가상 투자 심의 — 시스템 프롬프트 및 LangChain 체인 (UI 없음)."""

from __future__ import annotations

from typing import Any, Callable

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from gemini_common import make_llm

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


def build_estate_agent_chain(
    system_prompt: str,
    model_name: str,
    temperature: float,
    api_key: str,
) -> Callable[[str], str]:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "【심의 대상 물건 정보】\n{property_text}\n\n위 정보를 바탕으로 위원 역할에 맞게 분석·발언해 주세요.",
            ),
        ]
    )
    llm = make_llm(model_name, temperature, api_key)
    chain = prompt | llm | StrOutputParser()

    def _invoke(property_text: str, config: dict[str, Any] | None = None) -> str:
        return chain.invoke(property_text, config=config)

    return _invoke


def build_estate_summary_chain(
    model_name: str,
    temperature: float,
    api_key: str,
) -> Callable[[str, str, str, str], str]:
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
    llm = make_llm(model_name, temperature, api_key)
    chain = prompt | llm | StrOutputParser()

    def _invoke(
        property_text: str,
        a1: str,
        a2: str,
        a3: str,
        config: dict[str, Any] | None = None,
    ) -> str:
        return chain.invoke(
            {"property_text": property_text, "agent1": a1, "agent2": a2, "agent3": a3},
            config=config,
        )

    return _invoke

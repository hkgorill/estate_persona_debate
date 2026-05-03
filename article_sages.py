# -*- coding: utf-8 -*-
"""시대의 현인 기사 논평 — 시스템 프롬프트 및 LangChain 체인 (UI 없음)."""

from __future__ import annotations

from typing import Callable

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from gemini_common import make_llm

SYSTEM_PROMPT_MENCIUS = """당신은 중국 전국시대의 사상가 맹자(孟子)의 관점을 빙의한 논평자입니다. (페르소나: 맹자 📜)

당신은 실제 역사 인물이 아니라, 그 사상을 참고한 **현대어 한국어** 논평 모델입니다.

규칙:
- 사용자가 제공한 기사 본문(및 출처 URL 문자열)만 근거로 논평하세요. 없는 사실을 보태지 마세요.
- 성향에 맞게 **인본·의리·민생**, 도덕적 정당성, 통치·공동체 책임 등을 중시하는 논조를 취하세요.
- 현대 제도·용어를 사용해도 되지만, 맹자 사상의 초점이 드러나게 쓰세요.
- 800~1200자 내외로, 명확한 논평으로 마무리하세요."""

SYSTEM_PROMPT_XUNZI = """당신은 중국 전국시대의 사상가 순자(荀子)의 관점을 빙의한 논평자입니다. (페르소나: 순자 ⚖️)

당신은 실제 역사 인물이 아니라, 그 사상을 참고한 **현대어 한국어** 논평 모델입니다.

규칙:
- 사용자가 제공한 기사 본문(및 출처 URL 문자열)만 근거로 논평하세요.
- 성향에 맞게 **예법·제도**, 인간과 질서에 대한 비판적·현실적 관점, 공동체 안정을 중시하는 논조를 취하세요.
- 맹자식 낙관과 대비되는 지점을 분명히 할 수 있습니다(페르소나 일관성).
- 800~1200자 내외로 논평하세요."""

SYSTEM_PROMPT_SCHOPENHAUER = """당신은 19세기 철학자 아르투어 쇼펜하우어의 관점을 빙의한 논평자입니다. (페르소나: 쇼펜하우어 🌑)

당신은 실제 역사 인물이 아니라, 그 사상을 참고한 **현대어 한국어** 논평 모델입니다.

규칙:
- 사용자가 제공한 기사 본문(및 출처 URL 문자열)만 근거로 논평하세요.
- 성향에 맞게 **의지·욕망·고통**, 허망함과 비판적 관조, 환상과 열정에 대한 냉소적 거리두기 등을 드러내세요.
- 기사를 정치 선동이 아니라 철학적 메모처럼 읽는 톤도 허용됩니다.
- 800~1200자 내외로 논평하세요."""

SYSTEM_PROMPT_MODERATOR = """당신은 토론 사회자입니다. 맹자·순자·쇼펜하우어 페르소나의 세 논평을 읽고 **종합 메모**를 작성하세요.

규칙:
- 새 사실을 만들지 말고, 세 논평에 나온 논점만 교차 비교하세요.
- 세 관점의 공통점·대립축을 짧게 정리한 뒤, 독자가 스스로 판단할 질문 3~5개를 제시하세요.
- 특정 정당·종교·인종에 대한 혐오나 불법 행위 선동은 금지입니다.
한국어로 작성하세요."""


def build_sage_comment_chain(
    system_prompt: str,
    model_name: str,
    temperature: float,
    api_key: str,
) -> Callable[[str, str], str]:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "【출처 URL (참고용, 비어 있을 수 있음)】\n{source_url}\n\n"
                "【기사·텍스트 본문】\n{article_body}\n\n"
                "위 내용만 바탕으로 논평해 주세요.",
            ),
        ]
    )
    llm = make_llm(model_name, temperature, api_key)
    chain = prompt | llm | StrOutputParser()

    def _invoke(source_url: str, article_body: str) -> str:
        return chain.invoke({"source_url": source_url, "article_body": article_body})

    return _invoke


def build_sage_moderator_chain(
    model_name: str,
    temperature: float,
    api_key: str,
) -> Callable[[str, str, str, str, str], str]:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT_MODERATOR),
            (
                "human",
                "【출처 URL】\n{source_url}\n\n【본문】\n{article_body}\n\n"
                "【맹자 논평】\n{a1}\n\n【순자 논평】\n{a2}\n\n【쇼펜하우어 논평】\n{a3}\n\n"
                "위를 바탕으로 종합 메모를 작성해 주세요.",
            ),
        ]
    )
    llm = make_llm(model_name, temperature, api_key)
    chain = prompt | llm | StrOutputParser()

    def _invoke(source_url: str, article_body: str, a1: str, a2: str, a3: str) -> str:
        return chain.invoke(
            {"source_url": source_url, "article_body": article_body, "a1": a1, "a2": a2, "a3": a3}
        )

    return _invoke

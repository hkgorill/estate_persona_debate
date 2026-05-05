# -*- coding: utf-8 -*-
"""기사·텍스트 논평용 공통 LangChain 체인 (페르소나 시스템 프롬프트는 persona_presets 참조)."""

from __future__ import annotations

from typing import Any, Callable

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from gemini_common import make_llm


def build_article_comment_chain(
    system_prompt: str,
    model_name: str,
    temperature: float,
    api_key: str,
    *,
    body_field_label: str,
) -> Callable[[str, str], str]:
    """source_url, article_body 를 받아 논평 문자열을 반환합니다."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "【출처 URL (참고용, 비어 있을 수 있음)】\n{source_url}\n\n"
                f"【{body_field_label}】\n{{article_body}}\n\n"
                "위 내용만 바탕으로 논평해 주세요.",
            ),
        ]
    )
    llm = make_llm(model_name, temperature, api_key)
    chain = prompt | llm | StrOutputParser()

    def _invoke(
        source_url: str,
        article_body: str,
        config: dict[str, Any] | None = None,
    ) -> str:
        return chain.invoke(
            {"source_url": source_url, "article_body": article_body},
            config=config,
        )

    return _invoke


def build_freeform_moderator_chain(
    moderator_system_prompt: str,
    model_name: str,
    temperature: float,
    api_key: str,
) -> Callable[[str, str, str, str, str, str, str, str], str]:
    """
    source_url, article_body, display_name1..3, output1..3 를 받아 종합 메모를 반환합니다.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", moderator_system_prompt),
            (
                "human",
                "【출처 URL】\n{source_url}\n\n【본문】\n{article_body}\n\n"
                "【{n1}】\n{o1}\n\n【{n2}】\n{o2}\n\n【{n3}】\n{o3}\n\n"
                "위 세 논평을 바탕으로 종합 메모를 작성해 주세요.",
            ),
        ]
    )
    llm = make_llm(model_name, temperature, api_key)
    chain = prompt | llm | StrOutputParser()

    def _invoke(
        source_url: str,
        article_body: str,
        n1: str,
        o1: str,
        n2: str,
        o2: str,
        n3: str,
        o3: str,
        config: dict[str, Any] | None = None,
    ) -> str:
        return chain.invoke(
            {
                "source_url": source_url,
                "article_body": article_body,
                "n1": n1,
                "o1": o1,
                "n2": n2,
                "o2": o2,
                "n3": n3,
                "o3": o3,
            },
            config=config,
        )

    return _invoke

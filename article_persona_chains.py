# -*- coding: utf-8 -*-
"""기사·텍스트 논평용 공통 LangChain 체인 (페르소나 시스템 프롬프트는 persona_presets 참조)."""

from __future__ import annotations

from typing import Any, Callable

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from gemini_common import make_llm

ARTICLE_UNIFIED_MARKERS: tuple[str, str, str, str] = (
    "###P1###",
    "###P2###",
    "###P3###",
    "###MOD###",
)

_ARTICLE_UNIFIED_SYSTEM = """당신은 한 번의 응답으로 세 페르소나의 논평과 사회자 종합 메모를 작성합니다.

반드시 아래 **네 개의 시작 태그**를 이 순서만 사용하고, 각 태그는 **단독 줄**에 정확히 출력합니다.
태그 다음 줄부터 해당 역할의 본문만 작성합니다.

###P1###
(첫 번째 논평자 역할 본문만)
###P2###
(두 번째 논평자 역할 본문만)
###P3###
(세 번째 논평자 역할 본문만)
###MOD###
(사회자 종합 메모만 — 세 논평의 논점만 사용, 새 사실 금지)


【논평자 1 역할】
{prompt1}

【논평자 2 역할】
{prompt2}

【논평자 3 역할】
{prompt3}

【사회자】
{moderator_prompt}

추가 규칙:
- 제공된 URL·본문만 근거로 하세요.
- 논평 본문 안에서 위 태그 문자열을 반복·장식하지 마세요.
"""


def parse_article_unified_response(raw: str) -> tuple[str, str, str, str]:
    text = (raw or "").strip()
    tags = ARTICLE_UNIFIED_MARKERS
    out: list[str] = []
    for i, tag in enumerate(tags):
        start = text.find(tag)
        if start == -1:
            raise ValueError(f"응답에 구간 태그가 없습니다: {tag}")
        body_start = start + len(tag)
        if i + 1 < len(tags):
            nxt = text.find(tags[i + 1], body_start)
            if nxt == -1:
                raise ValueError(f"응답에 다음 태그가 없습니다: {tags[i + 1]}")
            out.append(text[body_start:nxt].strip())
        else:
            out.append(text[body_start:].strip())
    if len(out) != 4:
        raise ValueError("구간 분리 결과가 올바르지 않습니다.")
    return out[0], out[1], out[2], out[3]


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


def build_article_unified_chain(
    persona_prompts: tuple[str, str, str],
    moderator_system_prompt: str,
    model_name: str,
    temperature: float,
    api_key: str,
    *,
    body_field_label: str,
    persona_labels: tuple[str, str, str],
):
    """본문·URL을 한 번만 넣고 논평 3·종합 1을 한 번에 생성합니다 (토큰 절감)."""
    n1, n2, n3 = persona_labels
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _ARTICLE_UNIFIED_SYSTEM),
            (
                "human",
                "다음 URL·본문만 근거로 네 구간을 작성하세요.\n\n"
                "논평자 표시 이름(참고): 「{n1}」「{n2}」「{n3}」\n\n"
                "【출처 URL】\n{source_url}\n\n"
                "【{body_field_label}】\n{article_body}",
            ),
        ]
    )
    llm = make_llm(model_name, temperature, api_key)
    chain = prompt | llm | StrOutputParser()

    def _invoke(
        source_url: str,
        article_body: str,
        config: dict[str, Any] | None = None,
    ) -> tuple[str, str, str, str]:
        raw = chain.invoke(
            {
                "prompt1": persona_prompts[0],
                "prompt2": persona_prompts[1],
                "prompt3": persona_prompts[2],
                "moderator_prompt": moderator_system_prompt,
                "source_url": source_url,
                "article_body": article_body.strip(),
                "body_field_label": body_field_label,
                "n1": n1,
                "n2": n2,
                "n3": n3,
            },
            config=config,
        )
        return parse_article_unified_response(raw)

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

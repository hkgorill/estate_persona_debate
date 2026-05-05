# -*- coding: utf-8 -*-
"""LangChain Chat 모델 호출의 usage_metadata 합산 (Gemini 등)."""

from __future__ import annotations

from typing import Any, Final

from langchain_core.callbacks import UsageMetadataCallbackHandler

USAGE_NOTE: Final[str] = (
    "API usage_metadata 기준(청구 단위와 다를 수 있음). 동일 세션에서 여러 모델을 쓰면 모델별로 합산 후 표시합니다."
)


def new_usage_handler() -> UsageMetadataCallbackHandler:
    """한 번의 사용자 실행(여러 번 invoke)에 하나를 만들어 모든 호출에 같은 인스턴스를 넘기세요."""
    return UsageMetadataCallbackHandler()


def usage_invoke_config(handler: UsageMetadataCallbackHandler) -> dict[str, Any]:
    return {"callbacks": [handler]}


def merge_usage_totals(handler: UsageMetadataCallbackHandler) -> dict[str, Any]:
    """콜백에 누적된 usage를 모델별·전체 합계로 정리합니다."""
    tot_in = 0
    tot_out = 0
    tot_all = 0
    by_model: dict[str, dict[str, int]] = {}

    for model_name, meta in handler.usage_metadata.items():
        if not isinstance(meta, dict):
            continue
        inn = int(meta.get("input_tokens") or 0)
        out = int(meta.get("output_tokens") or 0)
        ttl_raw = meta.get("total_tokens")
        ttl = int(ttl_raw) if ttl_raw is not None else inn + out
        tot_in += inn
        tot_out += out
        tot_all += ttl
        by_model[str(model_name)] = {
            "input_tokens": inn,
            "output_tokens": out,
            "total_tokens": ttl,
        }

    return {
        "input_tokens": tot_in,
        "output_tokens": tot_out,
        "total_tokens": tot_all,
        "by_model": by_model,
    }


def format_usage_caption(totals: dict[str, Any]) -> str:
    """Streamlit caption 등에 넣을 한 줄 요약."""
    if not totals.get("by_model"):
        return "토큰: 이 실행에서 수집된 usage_metadata 가 없습니다."
    inn = int(totals.get("input_tokens") or 0)
    out = int(totals.get("output_tokens") or 0)
    ttl = int(totals.get("total_tokens") or 0)
    return f"토큰(API): 입력 {inn:,} · 출력 {out:,} · 합계 {ttl:,}"


def totals_for_notion_sheet(totals: dict[str, Any] | None) -> tuple[int, int, int]:
    if not totals:
        return 0, 0, 0
    return (
        int(totals.get("input_tokens") or 0),
        int(totals.get("output_tokens") or 0),
        int(totals.get("total_tokens") or 0),
    )

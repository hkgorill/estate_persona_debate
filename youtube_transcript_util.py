# -*- coding: utf-8 -*-
"""유튜브 URL에서 영상 ID 추출·자막 텍스트 수집 (youtube-transcript-api)."""

from __future__ import annotations

import re
from typing import Final

from youtube_transcript_api import (
    NoTranscriptFound,
    YouTubeTranscriptApi,
    YouTubeTranscriptApiException,
)

_VIDEO_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([0-9A-Za-z_-]{11})"
)


def extract_youtube_video_id(url: str) -> str | None:
    """watch / youtu.be / embed / shorts URL에서 11자 video id를 뽑습니다."""
    s = url.strip()
    if not s:
        return None
    m = _VIDEO_ID_RE.search(s)
    if m:
        return m.group(1)
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", s):
        return s
    return None


def _join_fetched(ft: object) -> str:
    snippets = getattr(ft, "snippets", None) or []
    parts: list[str] = []
    for sn in snippets:
        t = getattr(sn, "text", "") or ""
        t = t.replace("\n", " ").strip()
        if t:
            parts.append(t)
    return " ".join(parts).strip()


def fetch_transcript_plain_text(video_id: str) -> str:
    """
    자막(한국어·영어 우선)을 한 덩어리 텍스트로 가져옵니다.
    실패 시 YouTubeTranscriptApiException 계열이 전달됩니다.
    """
    api = YouTubeTranscriptApi()
    lang_tries: tuple[tuple[str, ...], ...] = (
        ("ko", "ko-KR", "en"),
        ("en",),
        ("ja", "en"),
    )
    for langs in lang_tries:
        try:
            ft = api.fetch(video_id, languages=langs)
            text = _join_fetched(ft)
            if text:
                return text
        except NoTranscriptFound:
            continue

    transcripts = list(api.list(video_id))
    if not transcripts:
        raise YouTubeTranscriptApiException("사용 가능한 자막 트랙이 없습니다.")

    for tr in transcripts:
        try:
            ft = tr.fetch()
            text = _join_fetched(ft)
            if text:
                return text
        except YouTubeTranscriptApiException:
            continue

    raise YouTubeTranscriptApiException("자막 텍스트를 비어 있지 않게 가져오지 못했습니다.")


def user_message_for_transcript_error(err: Exception) -> str:
    """Streamlit 등 UI에 보여 줄 짧은 한국어 안내."""
    name = type(err).__name__
    low = str(err).lower()
    if "transcriptsdisabled" in name.lower() or "disabled" in low:
        return "이 영상은 자막이 꺼져 있거나 제공되지 않습니다."
    if "notranscript" in name.lower() or "no transcript" in low:
        return "이 영상에서 가져올 수 있는 자막이 없습니다. (언어·자동생성 자막 여부를 확인해 주세요.)"
    if "videounavailable" in name.lower() or "unavailable" in low:
        return "영상을 찾을 수 없거나 비공개·삭제되었을 수 있습니다."
    if "invalid" in name.lower() and "video" in name.lower():
        return "유효하지 않은 영상 ID입니다."
    if "ipblocked" in name.lower() or "blocked" in low:
        return "YouTube 측에서 요청이 차단되었을 수 있습니다. 잠시 후 다시 시도해 주세요."
    return f"자막을 가져오는 중 오류가 났습니다: {err}"

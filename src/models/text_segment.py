from typing import Tuple

from pydantic import BaseModel


class TextSegment(BaseModel):
    original_timestamp: Tuple[float, float]
    text: str


class TextSegmentWithAudioTimestamp(TextSegment):
    audio_timestamp: Tuple[float, float]

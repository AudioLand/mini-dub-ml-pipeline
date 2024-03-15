from typing import Tuple

from pydantic import BaseModel


class TextSegment(BaseModel):
    original_timestamp: Tuple[float, float]
    text: str
    speaker: int = 0


class TextSegmentWithAudioTimestamp(TextSegment):
    audio_timestamp: Tuple[float, float]

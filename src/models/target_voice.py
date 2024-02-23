from typing import List

from pydantic import BaseModel

from models.voice_provider import VoiceProvider


class TargetVoice(BaseModel):
    voice_id: int
    voice_name: str
    provider: VoiceProvider
    original_id: str
    sample: str
    languages: List[str]

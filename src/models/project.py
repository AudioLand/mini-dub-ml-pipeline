from enum import Enum


class ProjectStatus(Enum):
    TRANSLATING = "translating"
    TRANSLATED = "translated"
    TRANSLATION_ERROR = "translationError"

from azure.ai.translation.text import TextTranslationClient, TranslatorCredential
from azure.ai.translation.text.models import InputTextItem

from configs.env import MICROSOFT_TRANSLATOR_API_KEY, MICROSOFT_TRANSLATOR_REGION
from configs.logger import print_info_log, catch_error
from constants.log_tags import LogTag

credentials = TranslatorCredential(
    key=MICROSOFT_TRANSLATOR_API_KEY,
    region=MICROSOFT_TRANSLATOR_REGION,
)

translator = TextTranslationClient(credential=credentials)


def translate_text_chunk_with_microsoft(
    text_chunk: str,
    language: str,
    project_id: str,
    show_logs: bool
) -> str:
    """
    Translates a given text into the specified language using Microsoft Translator.

    :param text_chunk: The text chunks to be translated.
    :param language: The target language for translation.
    :param project_id: The id of the processing project.
    :param show_logs: Determines whether to display logs while translating with gpt.

    Returns:
    - str: Translated text or original text if translation is not possible.
    """
    log_tag = LogTag.TRANSLATE_TEXT_CHUNK_WITH_MICROSOFT

    if show_logs:
        print_info_log(
            tag=log_tag,
            message=f"Translating text chunk: '{text_chunk}'"
        )

    translation_response = translator.translate(
        content=[InputTextItem(text=text_chunk)],
        to=[language],
    )

    if len(translation_response) == 0:
        catch_error(
            tag=log_tag,
            error=Exception(f"Microsoft could not translate text chunk: {text_chunk}"),
            project_id=project_id
        )

    # Get translated text from Microsoft response
    translated_text = translation_response[0].translations[0].text

    if show_logs:
        print_info_log(
            tag=log_tag,
            message=f"Text chunk translated:  {translated_text}"
        )

    return translated_text

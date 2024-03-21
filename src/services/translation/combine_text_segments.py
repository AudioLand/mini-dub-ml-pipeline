from typing import List

from configs.logger import print_info_log
from constants.log_tags import LogTag
from models.text_segment import TextSegment


def combine_text_segments(text_segments: List[TextSegment], show_logs: bool) -> str:
    """
    Combine the given TextSegments to the string, where segments are divided by [ and ] symbols.

    :param text_segments: The list of dictionaries with text segments and timestamps.
    :param show_logs: Determines whether to display logs while combining.

    :return: The string, where all text segments are divided by \\n symbol.
    """

    if show_logs:
        print_info_log(
            tag=LogTag.COMBINE_TEXT_SEGMENTS,
            message=f"Combining text chunks: {text_segments}"
        )

    formatted_text = ""
    for segment in text_segments:
        formatted_text += f" —\"{segment.text}\""

    if show_logs:
        print_info_log(
            tag=LogTag.COMBINE_TEXT_SEGMENTS,
            message=f"Combined text: {formatted_text}"
        )

    return formatted_text

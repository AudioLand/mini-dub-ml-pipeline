import re
from typing import List

from configs.logger import catch_error, print_info_log
from constants.log_tags import LogTag
from models.text_segment import TextSegment
from services.translation.combine_text_segments import combine_text_segments
from services.translation.split_text_to_chunks import split_text_to_chunks
from services.translation.translate_text_chunk_with_google import translate_text_chunk_with_google


def translate_text(
    text_segments: List[TextSegment],
    language: str,
    project_id: str,
    show_logs: bool = False
) -> List[TextSegment]:
    """
    Translate given text segments into the specified language.

    :param language: The target language for translation.
    :param text_segments: The list of TextSegments with original text segments and timestamps.
    :param project_id: The id of the processing project.
    :param show_logs: Determines whether to display logs while translating.

    :returns: The list of dictionaries with translated text segments and timestamps.
    """

    try:
        combined_text = combine_text_segments(
            text_segments=text_segments,
            show_logs=show_logs
        )
        text_chunks = split_text_to_chunks(
            text=combined_text,
            project_id=project_id,
            show_logs=show_logs
        )

        if show_logs:
            print_info_log(
                tag=LogTag.TRANSLATE_TEXT,
                message=f"Translating text chunks - {text_chunks}"
            )

        translated_text_chunks = []
        for chuck in text_chunks:
            translated_chunk = translate_text_chunk_with_google(
                language=language,
                text_chunk=chuck,
                project_id=project_id,
                show_logs=show_logs
            )
            translated_text_chunks.append(translated_chunk)

        if show_logs:
            print_info_log(
                tag=LogTag.TRANSLATE_TEXT,
                message=f"Translated text chunks: {translated_text_chunks}"
            )
            print_info_log(
                tag=LogTag.TRANSLATE_TEXT,
                message=f"Splitting translated chunks to segments by [ and ] symbols..."
            )

        # Split translated text to get original segments
        final_translated_text = "".join(translated_text_chunks)
        translated_text_segments: List[str] = re.findall(r"[^\[\]]+", final_translated_text)

        # Clear translated text with empty chunks
        while ' ' in translated_text_segments:
            translated_text_segments.remove(' ')

        if show_logs:
            print_info_log(
                tag=LogTag.TRANSLATE_TEXT,
                message=f"Split translated text segments: {translated_text_segments}"
            )

        original_segments_count = len(text_segments)
        translated_segments_count = len(translated_text_segments)
        for segment_index in range(min(original_segments_count, translated_segments_count)):
            translated_segment = translated_text_segments[segment_index]
            text_segments[segment_index].text = translated_segment

        return text_segments

    except Exception as e:
        catch_error(
            tag=LogTag.TRANSLATE_TEXT,
            error=e,
            project_id=project_id
        )


if __name__ == "__main__":
    test_text_segments = [
        TextSegment(original_timestamp=(0.0, 3.36), text=' I wake up in the morning and I want to reach for my phone,'),
        TextSegment(original_timestamp=(3.36, 5.74), text=' but I know that even if I were to crank up the brightness'),
        TextSegment(original_timestamp=(5.74, 7.0), text=' on that phone screen,'),
        TextSegment(original_timestamp=(7.0, 10.28), text=" it's not bright enough to trigger that cortisol spike."),
        TextSegment(original_timestamp=(10.28, 14.36),
                    text=' And for me to be at my most alert and focused throughout'),
        TextSegment(original_timestamp=(14.36, 16.16), text=' the day and to optimize my sleep at night.'),
        TextSegment(original_timestamp=(16.16, 20.2), text=' So what I do is I get out of bed and I go outside.'),
        TextSegment(original_timestamp=(20.2, 23.34), text=" And if it's a bright, clear day,"),
        TextSegment(original_timestamp=(23.34, 25.18), text=' and the sun is low in the sky,'),
        TextSegment(original_timestamp=(25.18, 27.18), text=' or the sun is starting to get overhead,'),
        TextSegment(original_timestamp=(27.18, 28.7), text=' what we call low solar angle,'),
        TextSegment(original_timestamp=(28.7, 31.74), text=" then I know I'm getting outside at the right time."),
        TextSegment(original_timestamp=(31.74, 34.78), text=" If there's cloud cover and I can't see the sun,"),
        TextSegment(original_timestamp=(34.78, 36.38), text=" I also know I'm doing a good thing,"),
        TextSegment(original_timestamp=(36.38, 38.56), text=' because it turns out, especially on cloudy days,'),
        TextSegment(original_timestamp=(38.56, 40.66), text=' you want to get outside and get as much light energy'),
        TextSegment(original_timestamp=(40.66, 42.42), text=' or photons in your eyes.'),
        TextSegment(original_timestamp=(42.42, 44.3), text=" But let's say it's a very clear day"),
        TextSegment(original_timestamp=(44.3, 46.44), text=' and I can see where the sun is.'),
        TextSegment(original_timestamp=(46.44, 49.24), text=' I do not need to stare directly into the sun.'),
        TextSegment(original_timestamp=(49.24, 52.2), text=" If it's very low in the sky, I might do that"),
        TextSegment(original_timestamp=(52.2, 54.52), text=" because it's not going to be very painful to my eyes."),
        TextSegment(original_timestamp=(54.52, 56.84), text=' However, if the sun is a little bit brighter.')
    ]
    test_target_language = "ru"
    test_project_id = "07fsfECkwma6fVTDyqQf"
    test_translated_text_segments = translate_text(
        text_segments=test_text_segments,
        language=test_target_language,
        project_id=test_project_id,
        show_logs=True
    )
    print(test_translated_text_segments)

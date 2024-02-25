import os
from typing import List, Tuple

from TTS.api import TTS
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from torch import cuda

from configs.logger import catch_error, print_info_log
from constants.files import PROCESSING_FILES_DIR_PATH
from constants.log_tags import LogTag
from models.text_segment import TextSegment, TextSegmentWithAudioTimestamp

DELAY_TO_WAIT_IN_SECONDS = 5 * 60

AUDIO_SEGMENT_PAUSE = 3000  # 3 sec

device = "cuda" if cuda.is_available() else "cpu"
shouldUseGPU = device == "cuda"
tts_model = "tts_models/multilingual/multi-dataset/xtts_v2"
TTS().download_model_by_name(tts_model)


def get_manager():
    manager = TTS().list_models()
    return manager


def get_models():
    manager = get_manager()
    print("Models:")
    print(manager.list_tts_models())


def get_langs():
    manager = get_manager()
    print("Langs:")
    print(manager.list_langs())


def add_audio_timestamps_to_segments(
    audio_file_path: str,
    text_segments: List[TextSegment],
    min_silence_len=2000,
    silence_thresh=-30,
    padding=500
):
    """
    Detects pauses in an audio file and adds audio_timestamps to segments.

    :param audio_file_path: Path to the audio file.
    :param text_segments: A list of text segments with 'timestamp' and 'text' keys.
    :param min_silence_len: Minimum length of silence to consider as a pause in milliseconds.
    :param silence_thresh: Silence threshold in dB.
    :param padding: Additional time in milliseconds to add to the end of each segment.
    :return: A list of tuples where each tuple is (start, end) time of pauses.
    """

    audio = AudioSegment.from_file(audio_file_path)
    speak_times = detect_nonsilent(
        audio_segment=audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )
    adjusted_speak_times: List[Tuple[float, float]] = []
    for start, end in speak_times:
        timestamps = max(start - padding, 0), min(end + padding, len(audio))
        adjusted_speak_times.append(timestamps)

    # Combine text segments and audio timestamps to one list
    combined_list: List[Tuple[TextSegment, Tuple[float, float]]] = list(
        zip(text_segments, adjusted_speak_times)
    )

    text_segments_with_audio_timestamps = []
    for segment, audio_timestamp in combined_list:
        text_segments_with_audio_timestamps.append(
            TextSegmentWithAudioTimestamp(
                **segment.dict(),  # Convert TextSegment to dict
                audio_timestamp=audio_timestamp
            )
        )
    return text_segments_with_audio_timestamps


def text_to_speech(
    text_segments: List[TextSegment],
    language: str,
    speaker_file_path: str,
    project_id: str,
    show_logs: bool = False
):
    # Check if the file exists
    if not os.path.exists(speaker_file_path):
        raise ValueError(f"File not found: {speaker_file_path}")

    translated_audio_file_path = f"{PROCESSING_FILES_DIR_PATH}/{project_id}-translated.mp3"
    full_text = ""

    # Convert segments to full text
    for segment in text_segments:
        full_text += segment.text

    try:
        tts = TTS(model_name=tts_model, gpu=shouldUseGPU).to(device)
        tts.tts_to_file(
            text=full_text,
            speaker_wav=speaker_file_path,
            language=language,
            file_path=translated_audio_file_path,
        )

        if show_logs:
            print_info_log(
                tag=LogTag.TEXT_TO_SPEECH,
                message=f"Translated audio save to {translated_audio_file_path}"
            )

        translated_text_segments_with_audio_timestamp = add_audio_timestamps_to_segments(
            audio_file_path=translated_audio_file_path,
            text_segments=text_segments
        )

        return translated_audio_file_path, translated_text_segments_with_audio_timestamp

    except Exception as e:
        catch_error(
            tag=LogTag.TEXT_TO_SPEECH,
            error=e,
            project_id=project_id
        )


# For local test
if __name__ == "__main__":
    test_text_segments = [
        TextSegment(original_timestamp=(0.0, 3.36), text='Я просыпаюсь утром и хочу потянуться к своему телефону,'),
        TextSegment(original_timestamp=(3.36, 5.74), text='но я знаю, что даже если бы я прибавил яркость'),
        TextSegment(original_timestamp=(5.74, 7.0), text='на экране этого телефона,'),
        TextSegment(original_timestamp=(7.0, 10.28),
                    text='она все равно не достаточно ярка, чтобы вызвать резкий прилив кортизола.'),
        TextSegment(original_timestamp=(10.28, 14.36),
                    text='И чтобы мне быть наиболее бодрым и сосредоточенным в течение'),
        TextSegment(original_timestamp=(14.36, 16.16), text='дня и оптимизировать свой сон ночью.'),
        TextSegment(original_timestamp=(16.16, 20.2), text='Поэтому я встаю с кровати и выхожу на улицу.'),
        TextSegment(original_timestamp=(20.2, 23.34), text='И если это яркий, чистый день,'),
        TextSegment(original_timestamp=(23.34, 25.18), text='и солнце низко в небе,'),
        TextSegment(original_timestamp=(25.18, 27.18), text='или уже начинает подниматься над головой,'),
        TextSegment(original_timestamp=(27.18, 28.7), text='то, что мы называем низким солнечным углом,'),
        TextSegment(original_timestamp=(28.7, 31.74), text='тогда я знаю, что вышел на улицу в правильное время.'),
        TextSegment(original_timestamp=(31.74, 34.78), text='Если небо затянуто облаками и я не вижу солнца,'),
        TextSegment(original_timestamp=(34.78, 36.38), text='то я также знаю, что делаю хорошее дело,'),
        TextSegment(original_timestamp=(36.38, 38.56), text='потому что оказывается, особенно в облачные дни,'),
        TextSegment(original_timestamp=(38.56, 40.66),
                    text='вы хотите выйти на улицу и получить как можно больше световой энергии'),
        TextSegment(original_timestamp=(40.66, 42.42), text='или фотонов в своих глазах.'),
        TextSegment(original_timestamp=(42.42, 44.3), text='Но допустим, это очень ясный день'),
        TextSegment(original_timestamp=(44.3, 46.44), text='и я вижу, где солнце.'),
        TextSegment(original_timestamp=(46.44, 49.24), text='Мне не нужно смотреть прямо на солнце.'),
        TextSegment(original_timestamp=(49.24, 52.2), text='Если оно очень низко в небе, я могу это сделать'),
        TextSegment(original_timestamp=(52.2, 54.52), text='потому что моим глазам это не причинит большой боли.'),
        TextSegment(original_timestamp=(54.52, 56.84), text='Однако, если солнце немного ярче.')
    ]
    test_project_id = "07fsfECkwma6fVTDyqQf"
    test_target_language = "ru"
    test_speaker_file_path = f"{PROCESSING_FILES_DIR_PATH}/syr-voice.ogg"
    test_translated_audio_file_path, test_translated_text_segments_with_audio_timestamp = text_to_speech(
        text_segments=test_text_segments,
        language=test_target_language,
        speaker_file_path=test_speaker_file_path,
        project_id=test_project_id,
        show_logs=True
    )
    print(test_translated_audio_file_path)
    print(test_translated_text_segments_with_audio_timestamp)

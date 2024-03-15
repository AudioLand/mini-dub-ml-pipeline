import os
from typing import List, Tuple

from TTS.api import TTS
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from torch import cuda
from whisper import load_audio

from configs.logger import catch_error, print_info_log
from constants.files import PROCESSING_FILES_DIR_PATH
from constants.log_tags import LogTag
from models.text_segment import TextSegment, TextSegmentWithAudioTimestamp
from services.text_to_speech.voice_detect import detect_voice

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
        project_id: str,
        is_cloning: bool,
        voice_ids: List[int],
        audio,
        show_logs: bool = False
):
    translated_audio_file_path = f"{PROCESSING_FILES_DIR_PATH}/{project_id}-translated.mp3"

    voices_samples = detect_voice(text_segments, language, voice_ids, is_cloning, audio)
    pause_segment = AudioSegment.silent(duration=AUDIO_SEGMENT_PAUSE)
    combined_audio = AudioSegment.empty()
    try:
        language = language[0:2].lower()
        for segment in text_segments:
            tts = TTS(model_name=tts_model, gpu=shouldUseGPU).to(device)
            segment_audio_path = f"{PROCESSING_FILES_DIR_PATH}/temp_segment.wav"
            tts.tts_to_file(
                text=segment.text,
                speaker_wav=voices_samples[segment.speaker],
                language=language,
                file_path=segment_audio_path,
            )
            segment_audio = AudioSegment.from_wav(segment_audio_path)
            combined_audio += segment_audio + pause_segment

        combined_audio.export(translated_audio_file_path, format="wav")
        translated_text_segments_with_audio_timestamp = add_audio_timestamps_to_segments(
            audio_file_path=translated_audio_file_path,
            text_segments=text_segments
        )

        if show_logs:
            print_info_log(
                tag=LogTag.TEXT_TO_SPEECH,
                message=f"Translated audio save to {translated_audio_file_path}"
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
    test_text_segments = [TextSegment(original_timestamp=(0.008488964346349746, 10.05942275042445),
                                      text='What about your development areas? What do you have identified as your '
                                           'greatest and biggest improvement areas? And what have you done to improve '
                                           'them so far?',
                                      speaker=1),
                          TextSegment(original_timestamp=(13.03056027164686, 22.555178268251275),
                                      text="What's in my greatest development area is my communication skills. I work "
                                           "on improving my ability to clearly convey my thoughts and ideas to "
                                           "others.",
                                      speaker=0),
                          TextSegment(original_timestamp=(23.658743633276742, 24.168081494057724), text=' Um.',
                                      speaker=0),
                          TextSegment(original_timestamp=(24.76230899830221, 28.344651952461803),
                                      text=" I've been working on proving by practicing my active listening.",
                                      speaker=0),
                          TextSegment(original_timestamp=(28.5144312393888, 29.431239388794566), text=' and um',
                                      speaker=0), TextSegment(original_timestamp=(29.92359932088285, 32.99660441426146),
                                                              text=' consciously hearing the ideas from other people.',
                                                              speaker=0)]
    test_project_id = "07fsfECkwma6fVTDyqQf"
    test_target_language = "English"
    voice_ids = [313, 97]
    language = "english"

    file_path = 'en_short_2_speakers.mp4'
    audio = load_audio(file_path)

    test_translated_audio_file_path, test_translated_text_segments_with_audio_timestamp = text_to_speech(
        text_segments=test_text_segments,
        language=test_target_language,
        is_cloning=False,
        voice_ids=voice_ids,
        project_id=test_project_id,
        audio=audio,
        show_logs=True
    )
    print(test_translated_audio_file_path)
    print(test_translated_text_segments_with_audio_timestamp)

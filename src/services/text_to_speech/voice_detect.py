import json

import numpy as np
import soundfile as sf
import requests
from whisper.audio import SAMPLE_RATE, load_audio

from configs.logger import print_info_log
from constants.files import PROCESSING_FILES_DIR_PATH
from constants.log_tags import LogTag
from models.text_segment import TextSegment

from typing import List


def download_audio(url, filename, show_logs=False):
    url = "https://speechki-book.s3.amazonaws.com/" + url
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
            if show_logs:
                print_info_log(
                    tag=LogTag.TEXT_TO_SPEECH,
                    message=f"File successfully saved as {filename}"
                )
            else:
                if show_logs:
                    print_info_log(
                        tag=LogTag.TEXT_TO_SPEECH,
                        message=f"Error downloading file {filename}"
                    )


def get_ordered_unique_voice_ids(text_segments):
    unique_voice_ids = []
    speakers = set()
    for segment in text_segments:
        if segment.speaker not in speakers:
            speakers.add(segment.speaker)
            unique_voice_ids.append(segment.speaker)
    return unique_voice_ids


# audio из whisper_load чтобы 2 раза не загружать.
def collect_voice_samples(text_segments: List[TextSegment], audio):
    voices_samples = {}
    # собрать в tmp по голосам файл
    for segment in text_segments:
        start, end = segment.original_timestamp
        if segment.speaker not in voices_samples:
            voices_samples[segment.speaker] = []
        voices_samples[segment.speaker].extend(audio[int(start * SAMPLE_RATE):int(end * SAMPLE_RATE)])
    voices_samples_files = {}
    for speaker, audio_segments in voices_samples.items():
        audio_temp_path = f"{PROCESSING_FILES_DIR_PATH}/sample_voice_{speaker}.wav"
        combined_audio = np.array(audio_segments)
        sf.write(audio_temp_path, combined_audio, SAMPLE_RATE)
        voices_samples_files[speaker] = audio_temp_path
    return voices_samples_files


def collect_prepared_voice_samples(voice_ids):
    voice_ids_rez = {}

    with open('configs/tts-voices.json', 'r', encoding='utf-8') as file:
        voices_json = json.load(file)
        for voice in voices_json:
            if voice['voice_id'] in voice_ids:
                filename = f"{PROCESSING_FILES_DIR_PATH}/voice_{voice['voice_id']}.ogg"
                download_audio(voice['sample'], filename)
                voice_ids_rez[voice['voice_id']] = filename
    return voice_ids_rez


def collect_voice_by_language(language: str):
    filename = f"{PROCESSING_FILES_DIR_PATH}/ex-voice.ogg"

    # Открываем определенный конфиг с подготовленными голосами
    with open('configs/tts-voices.json', 'r', encoding='utf-8') as file:
        voices_json = json.load(file)
        for voice in voices_json:
            if language.lower() in voice['languages']:
                download_audio(voice['sample'], filename)
                return {0: filename}


def detect_voice(
        text_segments: List[TextSegment],
        language: str,
        voice_ids: List[int],
        is_cloning: bool,
        audio):
    if is_cloning:
        return collect_voice_samples(text_segments, audio)
    elif voice_ids and len(voice_ids) > 0:
        unique_speaker = get_ordered_unique_voice_ids(text_segments)
        # TODO change to exception
        assert len(unique_speaker) == len(voice_ids)
        voice_ids_rez = collect_prepared_voice_samples(set(voice_ids))
        result = {}
        def_voice = collect_voice_by_language(language)[0]
        for speaker, voice_id in zip(unique_speaker, voice_ids):
            if voice_id in voice_ids_rez:
                result[speaker] = voice_ids_rez[voice_id]
            else:
                result[speaker] = def_voice
        return result
    else:
        return collect_voice_by_language(language)


# TESTS ==================================================================
def test_detect_voice_with_voice_ids(test_text_segments, audio):
    voice_ids = [313, 97]
    language = "english"
    is_cloning = False

    result = detect_voice(test_text_segments, language, voice_ids, is_cloning, audio)

    assert result is not None
    assert len(result) == len(set([segment.speaker for segment in test_text_segments]))

    return result


def test_detect_voice_with_empty_voice_ids(test_text_segments, audio):
    voice_ids = []
    language = "English"
    is_cloning = False

    result = detect_voice(test_text_segments, language, voice_ids, is_cloning, audio)

    return result


if __name__ == "__main__":
    file_path = 'en_short_2_speakers.mp4'
    audio = load_audio(file_path)
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
    print(collect_voice_samples(test_text_segments, audio))
    print(test_detect_voice_with_voice_ids(test_text_segments, audio))
    print(test_detect_voice_with_empty_voice_ids(test_text_segments, audio))

import os
import re

import torch
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from pyannote.audio import Pipeline
from whisper import load_model, load_audio
from whisper.audio import SAMPLE_RATE

from configs.logger import catch_error, print_info_log
from constants.files import PROCESSING_FILES_DIR_PATH
from constants.log_tags import LogTag
from constants.whisper_model import WhisperModel
from models.text_segment import TextSegment

# Load whisper model by name
model = load_model(WhisperModel.BASE)


# Функция для проверки расширения файла
def check_audio_format(file_path, desired_format=".wav"):
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower() == desired_format


def transcribe_segment(audio, start, end):
    audio_segment = audio[int(start * SAMPLE_RATE):int(end * SAMPLE_RATE)]

    result = model.transcribe(audio_segment)
    return result['text']


def speech_to_text(file_path: str, project_id: str, is_cloning: bool, show_logs: bool = False, num_speakers: int = None,
                   processed_project_is_video: bool = False):
    """Convert the audio content of file into text."""

    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        if show_logs:
            print_info_log(
                tag=LogTag.SPEECH_TO_TEXT,
                message=f"Converting speech to text of {file_path}"
            )

        audio = load_audio(file_path)

        transcript_parts = []

        if is_cloning or (num_speakers and num_speakers > 1):
            audio_temp_path = f"{PROCESSING_FILES_DIR_PATH}/orig.wav"
            if processed_project_is_video:
                # Обрабатываем видео файл: извлекаем аудио
                video = VideoFileClip(file_path)
                audio_temp = video.audio
                audio_temp.write_audiofile(audio_temp_path)
            else:
                # Проверяем формат аудио файла
                if check_audio_format(file_path):
                    audio_temp_path = file_path
                else:
                    # Конвертируем аудио файл в WAV
                    audio_temp = AudioFileClip(file_path)
                    audio_temp.write_audiofile(audio_temp_path)

            # TODO: speakers number.
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1",
                                                use_auth_token=os.getenv("HUGGING_FACE_TOKEN"))

            if torch.cuda.is_available():
                pipeline.to(torch.device("cuda"))
            diarization = pipeline(audio_temp_path, num_speakers=num_speakers)
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start, end = turn.start, turn.end
                transcript = transcribe_segment(audio, start, end)
                if show_logs:
                    print_info_log(
                        tag=LogTag.SPEECH_TO_TEXT,
                        message=f"Speaker {speaker}: {transcript}"
                    )
                number = re.findall('\\d+', speaker)
                transcript_parts.append(TextSegment(
                    original_timestamp=(start, end),
                    text=transcript,
                    speaker=int(number[0])
                ))
        else:
            result = model.transcribe(
                audio,
                temperature=1.0,
                no_speech_threshold=0.2,
            )
            transcript_parts = [TextSegment(
                original_timestamp=(segment['start'], segment['end']),
                text=segment['text']
            ) for segment in result["segments"]]

        return transcript_parts, audio

    except ValueError as ve:
        catch_error(
            tag=LogTag.SPEECH_TO_TEXT,
            error=ve,
            project_id=project_id
        )


if __name__ == "__main__":
    test_project_id = "07fsfECkwma6fVTDyqQf"
    test_file_path = f"{PROCESSING_FILES_DIR_PATH}/{test_project_id}.mp4"
    test_transcript_parts = speech_to_text(
        file_path=test_file_path,
        project_id=test_project_id,
        is_cloning=True,
        show_logs=True
    )
    print(test_transcript_parts)

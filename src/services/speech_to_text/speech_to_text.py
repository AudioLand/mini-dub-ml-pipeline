import os
from typing import List

from whisper import load_model, load_audio

from configs.logger import catch_error, print_info_log
from constants.files import PROCESSING_FILES_DIR_PATH
from constants.log_tags import LogTag
from constants.whisper_model import WhisperModel
from models.text_segment import TextSegment

# Load whisper model by name
model = load_model(WhisperModel.BASE)


def speech_to_text(file_path: str, project_id: str, show_logs: bool = False) -> List[TextSegment]:
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
        result = model.transcribe(
            audio,
            temperature=1.0,
            no_speech_threshold=0.2,
        )
        transcript_parts = [TextSegment(
            original_timestamp=(segment['start'], segment['end']),
            text=segment['text']
        ) for segment in result["segments"]]

        return transcript_parts

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
        show_logs=True
    )
    print(test_transcript_parts)

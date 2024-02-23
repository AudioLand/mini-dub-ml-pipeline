import os
from datetime import datetime

from fastapi import APIRouter

from configs.logger import print_info_log, catch_error
from constants.files import PROCESSING_FILES_DIR_PATH
from constants.log_tags import LogTag
from models.file_type import FileType
from models.project import ProjectStatus
from services.firebase.firestore.update_project import update_project_status_and_translated_link_by_id
from services.firebase.storage.download_blob import download_blob
from services.firebase.storage.upload_blob import upload_blob
from services.overlay.overlay_audio_to_video import overlay_audio_to_video
from services.speech_to_text.speech_to_text import speech_to_text
from services.text_to_speech.text_to_speech import text_to_speech
from services.translation.translate_text import translate_text
from utils.files import get_file_extension, get_file_type, get_file_dir, get_file_name

dub_router = APIRouter(tags=["DUB"])


@dub_router.get("/")
def generate(
    project_id: str,
    target_language: str,
    original_file_location: str,
    voice_file_path: str,
):
    """
    Generates a dubbed version of the original video or audio file in the target language
    and update user's used tokens in seconds.

    :param project_id: The id of the processing project.
    :param target_language: The language in which the video will be dubbed.
    :param original_file_location: The location of the original video file in the cloud storage.
    :param voice_file_path: The location of the user voice in the cloud storage.

    :return: Upload the dubbed video to Firebase Cloud Storage

    :Example:
    >>> generate(
    ...     project_id=f"07fsfECkwma6fVTDyqQf",
    ...     target_language="Russian",
    ...     original_file_location="z8Z5j71WbmhaioUHDHh5KrBqEO13/07fsfECkwma6fVTDyqQf/test-video-1min.mp4",
    ...     speaker_file_path="z8Z5j71WbmhaioUHDHh5KrBqEO13/07fsfECkwma6fVTDyqQf/voice.mp4",
    ... )
    Check if project_id and original_file_location exist in Firebase
    """

    try:
        start_time = datetime.now()
        print_info_log(
            tag=LogTag.MAIN,
            message=f"Job Started! Processing project with id {project_id}..."
        )

        """Download project file from Cloud Storage"""

        print_info_log(
            tag=LogTag.MAIN,
            message="Downloading media file from Cloud Storage..."
        )

        source_blob_path = original_file_location
        # Extract extension from the original file location
        original_file_extension = get_file_extension(original_file_location)
        # Combine project_id with the extracted extension
        local_original_file_path = f"{PROCESSING_FILES_DIR_PATH}/{project_id}.{original_file_extension}"
        # Download file
        download_blob(
            source_blob_path=source_blob_path,
            destination_file_path=local_original_file_path,
            project_id=project_id,
            show_logs=True
        )

        print_info_log(
            tag=LogTag.MAIN,
            message="Media file downloaded."
        )

        """Change project status to "translating"""

        print_info_log(
            tag=LogTag.MAIN,
            message="Updating project status to 'translating'..."
        )

        update_project_status_and_translated_link_by_id(
            project_id=project_id,
            status=ProjectStatus.TRANSLATING.value,
            translated_file_link="",
            show_logs=True
        )

        print_info_log(
            tag=LogTag.MAIN,
            message="Project status updated."
        )

        """Convert file speech to text"""

        print_info_log(
            tag=LogTag.MAIN,
            message="Starting speech to text..."
        )

        original_text_segments = speech_to_text(
            file_path=local_original_file_path,
            project_id=project_id,
            show_logs=True
        )

        print_info_log(
            tag=LogTag.MAIN,
            message="Speech to text completed."
        )

        """Translate text"""

        print_info_log(
            tag=LogTag.MAIN,
            message="Translating text..."
        )

        translated_text_segments = translate_text(
            text_segments=original_text_segments,
            language=target_language,
            project_id=project_id,
            show_logs=True
        )

        print_info_log(
            tag=LogTag.MAIN,
            message="Translation completed."
        )

        """Download user voice for voice cloning in TTS"""

        print_info_log(
            tag=LogTag.MAIN,
            message="Downloading user voice for cloning from Cloud Storage..."
        )

        voice_blob_path = voice_file_path
        # Extract extension from the voice file location
        voice_file_extension = get_file_extension(voice_file_path)
        # Combine project_id with the extracted extension
        local_voice_file_path = f"{PROCESSING_FILES_DIR_PATH}/{project_id}-voice.{voice_file_extension}"
        # Download file
        download_blob(
            source_blob_path=voice_blob_path,
            destination_file_path=local_voice_file_path,
            project_id=project_id,
            show_logs=True
        )

        print_info_log(
            tag=LogTag.MAIN,
            message="User voice downloaded."
        )

        """Generate audio from translated text"""

        print_info_log(
            tag=LogTag.MAIN,
            message="Text to speech..."
        )

        local_translated_audio_path, translated_text_segments_with_audio_timestamp = text_to_speech(
            text_segments=translated_text_segments,
            language=target_language,
            speaker_file_path=local_voice_file_path,
            project_id=project_id,
            show_logs=True
        )

        print_info_log(
            tag=LogTag.MAIN,
            message="Text to speech completed."
        )

        """Overlay audio to video"""

        processed_project_is_video = get_file_type(local_original_file_path) == FileType.VIDEO
        # Overlay audio if project is video
        if processed_project_is_video:
            print_info_log(
                tag=LogTag.MAIN,
                message="Overlay audio to video..."
            )

            local_translated_file_path = overlay_audio_to_video(
                video_path=local_original_file_path,
                audio_path=local_translated_audio_path,
                text_segments_with_audio_timestamp=translated_text_segments_with_audio_timestamp,
                project_id=project_id,
                remove_original_audio=True,
                speedup_slow_audio=False,
                show_logs=True
            )

            print_info_log(
                tag=LogTag.MAIN,
                message="Overlay audio completed."
            )

        # Unless return translated audio
        else:
            local_translated_file_path = local_translated_audio_path

        """Upload audio to cloud storage"""

        # Extract the path and filename from the original_file_location
        original_file_dir = get_file_dir(original_file_location)
        original_file_name = get_file_name(original_file_location)
        original_file_suffix = get_file_extension(original_file_location)

        # Create the destination blob name with '-translated' appended to the filename
        destination_blob_name = f"{original_file_dir}/{original_file_name}-translated.{original_file_suffix}"

        print_info_log(
            tag=LogTag.MAIN,
            message="Uploading translated file to cloud storage..."
        )

        file_public_link = upload_blob(
            source_file_name=local_translated_file_path,
            destination_blob_name=destination_blob_name,
            project_id=project_id,
            show_logs=True
        )

        print_info_log(
            tag=LogTag.MAIN,
            message=f"File uploaded to cloud storage, destination_blob_name - {destination_blob_name}"
        )

        """Remove all processed files"""

        print_info_log(
            tag=LogTag.MAIN,
            message="Removing all project processed files..."
        )

        # Remove original file
        os.remove(local_original_file_path)
        os.remove(local_voice_file_path)
        # Remove translated file
        if processed_project_is_video:
            os.remove(local_translated_file_path)
            os.remove(local_translated_audio_path)
        else:
            os.remove(local_translated_file_path)

        print_info_log(
            tag=LogTag.MAIN,
            message="Removing completed."
        )

        """Change project status to "translated"""

        print_info_log(
            tag=LogTag.MAIN,
            message="Updating project status to 'translated'..."
        )

        update_project_status_and_translated_link_by_id(
            project_id=project_id,
            status=ProjectStatus.TRANSLATED.value,
            translated_file_link=file_public_link,
            show_logs=True
        )

        print_info_log(
            tag=LogTag.MAIN,
            message="Project status updated."
        )

        end_time = datetime.now()
        time_difference = end_time - start_time

        print_info_log(
            tag=LogTag.MAIN,
            message=f"Job Done! Project translation time: {time_difference}"
        )

        return {"status": "it is working!!!"}

    except Exception as e:
        catch_error(
            tag=LogTag.MAIN,
            error=e,
            project_id=project_id
        )


if __name__ == "__main__":
    test_user_id = "z8Z5j71WbmhaioUHDHh5KrBqEO13"
    test_project_id = "07fsfECkwma6fVTDyqQf"
    test_media_file_name = "test-video-1min.mp4"
    test_voice_file_name = "voice.mp3"
    test_target_language = "ru"
    test_original_file_location = f"{test_user_id}/{test_project_id}/{test_media_file_name}"
    test_voice_file_location = f"{test_user_id}/{test_project_id}/{test_voice_file_name}"
    generate(
        project_id=test_project_id,
        target_language=test_target_language,
        original_file_location=test_original_file_location,
        voice_file_path=test_voice_file_location,
    )

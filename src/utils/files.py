from pathlib import Path

from constants.files import VIDEO_SUPPORTED_EXTENSIONS, AUDIO_SUPPORTED_EXTENSIONS
from models.file_type import FileType


def get_file_extension(file_path: str) -> str:
    file_suffix = Path(file_path).suffix.replace('.', '')
    return file_suffix


def get_file_dir(file_path: str) -> str:
    file_dir = str(Path(file_path).parent)
    return file_dir


def get_file_name(file_path: str) -> str:
    file_name = Path(file_path).stem
    return file_name


def get_file_type(file_path: str) -> FileType:
    file_extension = get_file_extension(file_path)

    if file_extension in VIDEO_SUPPORTED_EXTENSIONS:
        return FileType.VIDEO
    elif file_extension in AUDIO_SUPPORTED_EXTENSIONS:
        return FileType.AUDIO
    else:
        raise Exception(f"Unsupported file type with extension: {file_extension}")


if __name__ == "__main__":
    test_file_path = "video.mp4"
    # test_file_path = "video.ext"  # For raise Exception

    test_file_suffix = get_file_extension(test_file_path)
    print(test_file_suffix)

    test_file_type = get_file_type(test_file_path)
    print(test_file_type)

    print(test_file_type == FileType.VIDEO)
    print(test_file_type == "video")

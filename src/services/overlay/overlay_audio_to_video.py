import os
import tempfile
from typing import List

from audiostretchy.stretch import stretch_audio
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment

from configs.logger import catch_error, print_info_log
from constants.codecs import MP4_CODEC
from constants.files import VIDEO_SUPPORTED_EXTENSIONS, AUDIO_SUPPORTED_EXTENSIONS, PROCESSING_FILES_DIR_PATH
from constants.log_tags import LogTag
from models.text_segment import TextSegmentWithAudioTimestamp
from services.overlay.lower_volume_in_segments import lower_volume_in_segments
from utils.files import get_file_extension, get_file_name


def overlay_audio_to_video(
    video_path: str,
    audio_path: str,
    text_segments_with_audio_timestamp: List[TextSegmentWithAudioTimestamp],
    project_id: str,
    remove_original_audio: bool = False,
    speedup_slow_audio: bool = True,
    show_logs: bool = False
):
    try:
        if show_logs:
            print_info_log(
                tag=LogTag.OVERLAY_AUDIO,
                message=f"Overlaying text_segments - {text_segments_with_audio_timestamp}"
            )

        video_file_name = get_file_name(video_path)
        video_file_suffix = get_file_extension(video_path)
        audio_file_suffix = get_file_extension(audio_path)

        # Check if paths exist
        if not os.path.exists(video_path):
            catch_error(
                tag=LogTag.OVERLAY_AUDIO,
                error=ValueError(f"Video path {video_path} does not exist."),
                project_id=project_id
            )
        if not os.path.exists(audio_path):
            catch_error(
                tag=LogTag.OVERLAY_AUDIO,
                error=ValueError(f"Audio path {audio_path} does not exist."),
                project_id=project_id
            )

        # Check for supported file extensions
        if video_file_suffix not in VIDEO_SUPPORTED_EXTENSIONS:
            catch_error(
                tag=LogTag.OVERLAY_AUDIO,
                error=ValueError(
                    f"Invalid video format: {video_file_suffix}. Only {VIDEO_SUPPORTED_EXTENSIONS} are supported."
                ),
                project_id=project_id
            )
        if audio_file_suffix not in AUDIO_SUPPORTED_EXTENSIONS:
            catch_error(
                tag=LogTag.OVERLAY_AUDIO,
                error=ValueError(
                    f"Invalid audio format: {audio_file_suffix}. Only {AUDIO_SUPPORTED_EXTENSIONS} are supported."
                ),
                project_id=project_id
            )

        translated_video_path = f"{PROCESSING_FILES_DIR_PATH}/{video_file_name}-translated.{video_file_suffix}"

        original_video = VideoFileClip(video_path)
        original_video_duration = original_video.duration
        translated_audio = AudioFileClip(audio_path)

        if show_logs:
            print_info_log(
                tag=LogTag.OVERLAY_AUDIO,
                message=f"Input video duration: {original_video_duration}s"
            )
            print_info_log(
                tag=LogTag.OVERLAY_AUDIO,
                message=f"Input audio duration: {translated_audio.duration}s"
            )

        final_audio = AudioSegment.from_file(video_path, format=video_file_suffix)

        # Remove original video sound
        if remove_original_audio:
            if show_logs:
                print_info_log(
                    tag=LogTag.OVERLAY_AUDIO,
                    message=f"Remove original video sound."
                )
            final_audio = final_audio.silent(duration=original_video_duration * 1000)
        else:
            final_audio = lower_volume_in_segments(final_audio, text_segments_with_audio_timestamp, 15)

        for segment in text_segments_with_audio_timestamp:
            if show_logs:
                print_info_log(
                    tag=LogTag.OVERLAY_AUDIO,
                    message=f"Processing segment {segment}"
                )

            video_start_time, video_end_time = segment.original_timestamp
            video_duration = (video_end_time - video_start_time) * 1000

            audio_start_time, audio_end_time = segment.audio_timestamp
            audio_segment = AudioSegment.from_file(audio_path)[audio_start_time:audio_end_time]
            audio_duration = audio_end_time - audio_start_time

            if show_logs:
                print_info_log(
                    tag=LogTag.OVERLAY_AUDIO,
                    message=f"Video segment duration: {video_duration:.2f}ms | {video_duration / 1000:.2f}s"
                )
                print_info_log(
                    tag=LogTag.OVERLAY_AUDIO,
                    message=f"Audio segment duration: {audio_duration:.2f}ms | {audio_duration / 1000:.2f}s"
                )

            # Speed up audio if it's need
            if speedup_slow_audio:
                if audio_duration - video_duration > 0.5:
                    # ratio = audio_duration / video_duration
                    ratio = video_duration / audio_duration
                    # Do not use "with", because temp file will not be deleted
                    temp_file = tempfile.NamedTemporaryFile(
                        dir=f"{PROCESSING_FILES_DIR_PATH}/",
                        suffix=".wav",
                        delete=True
                    )
                    stretched_audio_file_path = f"stretched-audio-segment-{project_id}.wav"
                    audio_segment.export(temp_file.name, format="wav")
                    stretch_audio(temp_file.name, stretched_audio_file_path, ratio)
                    audio_segment = AudioSegment.from_file(stretched_audio_file_path)
                    # Close and auto-delete temp file
                    temp_file.close()
                    # Delete stretched audio segment file
                    os.remove(stretched_audio_file_path)

                    if show_logs:
                        print_info_log(
                            tag=LogTag.OVERLAY_AUDIO,
                            message=f"Speeding up audio by a factor of: {ratio:.2f}"
                        )

            final_audio = final_audio.overlay(audio_segment, position=video_start_time * 1000)
            if show_logs:
                print_info_log(
                    tag=LogTag.OVERLAY_AUDIO,
                    message=f"Overlaying audio at {video_start_time:.2f}s in video."
                )

        if show_logs:
            print_info_log(
                tag=LogTag.OVERLAY_AUDIO,
                message=f"Processing all segments completed."
            )

        overlay_audio_name = f"overlay-audio-{project_id}.mp3"
        final_audio.export(overlay_audio_name, format="mp3")
        final_audio_clip = AudioFileClip(overlay_audio_name)

        # Set the audio of the video to the new audio clip
        final_video = original_video.set_audio(final_audio_clip)

        if show_logs:
            print_info_log(
                tag=LogTag.OVERLAY_AUDIO,
                message=f"Output video duration: {final_video.duration}"
            )
            print_info_log(
                tag=LogTag.OVERLAY_AUDIO,
                message=f"Output audio duration: {final_audio_clip.duration}"
            )

        final_video.write_videofile(
            filename=translated_video_path,
            codec=MP4_CODEC,
            fps=original_video.fps,
            logger=None
        )

        # TODO: use clean FFmpeg
        # input_video = ffmpeg.input(video_path)
        # input_audio = ffmpeg.input(audio_path)
        # ffmpeg.concat(input_video, input_audio, v=1, a=1).output(str(translated_video_path)).run()  # Error here

        # Close the clips to free up memory
        final_video.close()
        translated_audio.close()
        # Remove audio overlay file
        os.remove(overlay_audio_name)

        if show_logs:
            print_info_log(
                tag=LogTag.OVERLAY_AUDIO,
                message=f"Overlay video saved to {translated_video_path}"
            )

        return translated_video_path

    except Exception as e:
        catch_error(
            tag=LogTag.OVERLAY_AUDIO,
            error=e,
            project_id=project_id
        )


# For local test
if __name__ == "__main__":
    test_text_segments_with_audio_timestamps = [
        TextSegmentWithAudioTimestamp(original_timestamp=(0.0, 3.36),
                                      text='Я просыпаюсь утром и хочу потянуться к своему телефону,',
                                      audio_timestamp=(2850.0, 6957.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(3.36, 5.74),
                                      text='но я знаю, что даже если бы я прибавил яркость',
                                      audio_timestamp=(9446.0, 12723.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(5.74, 7.0), text='на экране этого телефона,',
                                      audio_timestamp=(15398.0, 17503.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(7.0, 10.28),
                                      text='она все равно не достаточно ярка, чтобы вызвать резкий прилив кортизола.',
                                      audio_timestamp=(19941.0, 24929.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(10.28, 14.36),
                                      text='И чтобы мне быть наиболее бодрым и сосредоточенным в течение',
                                      audio_timestamp=(28447.0, 32586.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(14.36, 16.16), text='дня и оптимизировать свой сон ночью.',
                                      audio_timestamp=(35128.0, 37793.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(16.16, 20.2),
                                      text='Поэтому я встаю с кровати и выхожу на улицу.',
                                      audio_timestamp=(41272.0, 44726.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(20.2, 23.34), text='И если это яркий, чистый день,',
                                      audio_timestamp=(48258.0, 50784.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(23.34, 25.18), text='и солнце низко в небе,',
                                      audio_timestamp=(53158.0, 55199.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(25.18, 27.18),
                                      text='или уже начинает подниматься над головой,',
                                      audio_timestamp=(57661.0, 60527.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(27.18, 28.7),
                                      text='то, что мы называем низким солнечным углом,',
                                      audio_timestamp=(62941.0, 66104.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(28.7, 31.74),
                                      text='тогда я знаю, что вышел на улицу в правильное время.',
                                      audio_timestamp=(68637.0, 72079.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(31.74, 34.78),
                                      text='Если небо затянуто облаками и я не вижу солнца,',
                                      audio_timestamp=(75457.0, 79046.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(34.78, 36.38),
                                      text='то я также знаю, что делаю хорошее дело,',
                                      audio_timestamp=(81580.0, 84705.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(36.38, 38.56),
                                      text='потому что оказывается, особенно в облачные дни,',
                                      audio_timestamp=(87238.0, 90644.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(38.56, 40.66),
                                      text='вы хотите выйти на улицу и получить как можно больше световой энергии',
                                      audio_timestamp=(93249.0, 97974.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(40.66, 42.42), text='или фотонов в своих глазах.',
                                      audio_timestamp=(100556.0, 102790.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(42.42, 44.3), text='Но допустим, это очень ясный день',
                                      audio_timestamp=(106297.0, 109257.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(44.3, 46.44), text='и я вижу, где солнце.',
                                      audio_timestamp=(111689.0, 113779.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(46.44, 49.24), text='Мне не нужно смотреть прямо на солнце.',
                                      audio_timestamp=(117313.0, 120052.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(49.24, 52.2),
                                      text='Если оно очень низко в небе, я могу это сделать',
                                      audio_timestamp=(123560.0, 127346.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(52.2, 54.52),
                                      text='потому что моим глазам это не причинит большой боли.',
                                      audio_timestamp=(129914.0, 133599.0)),
        TextSegmentWithAudioTimestamp(original_timestamp=(54.52, 56.84), text='Однако, если солнце немного ярче.',
                                      audio_timestamp=(136943.0, 139977.0))
    ]
    test_project_id = "u4eep3w19GImXUqnbPWc"
    test_video_path = f"{PROCESSING_FILES_DIR_PATH}/{test_project_id}.mp4"
    test_audio_path = f"{PROCESSING_FILES_DIR_PATH}/{test_project_id}-translated.mp3"
    overlay_audio_to_video(
        video_path=test_video_path,
        audio_path=test_audio_path,
        text_segments_with_audio_timestamp=test_text_segments_with_audio_timestamps,
        project_id=test_project_id,
        show_logs=True
    )

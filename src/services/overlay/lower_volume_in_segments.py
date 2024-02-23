from typing import List
from pydub import AudioSegment
from models.text_segment import TextSegmentWithAudioTimestamp


def lower_volume_in_segments(audio: AudioSegment, segments: List[TextSegmentWithAudioTimestamp],
                             reduction_dB: float) -> AudioSegment:
    """
    Lowers the volume of specified segments in an audio file.

    :param audio: The original AudioSegment object.
    :param segments: A list of instances, each containing the start and end times of segments.
    :param reduction_dB: The amount of volume reduction in decibels.
    :return: A new AudioSegment with the volume reduced in the specified segments.
    """
    # Start with an empty audio segment
    modified_audio = AudioSegment.silent(duration=0)

    last_end = 0
    for segment in segments:
        start, end = segment.original_timestamp
        start *= 1000
        end *= 1000
        # Add the segment before the current affected segment
        modified_audio += audio[last_end:start]

        # Reduce volume for the current segment and add it
        affected_segment = audio[start:end] - reduction_dB
        modified_audio += affected_segment

        last_end = end

    # Add the remaining part of the audio, if any
    modified_audio += audio[last_end:]
    return modified_audio
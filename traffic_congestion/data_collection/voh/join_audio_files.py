import glob
from pathlib import Path

from pydub import AudioSegment

if __name__ == '__main__':
    # Read all audio files
    audio_files = sorted(list(glob.glob("./*.aac")))
    audio_segments = [
        AudioSegment.from_file(audio_file, format="aac")
        for audio_file in audio_files
    ]

    # Simple export
    joined = sum(audio_segments)
    joined.export("./{}_to_{}.wav".format(
        Path(audio_files[0]).stem,
        Path(audio_files[-1]).stem),
                  format="wav")

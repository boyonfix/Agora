import os
import time
from pydub import AudioSegment


RAW_WAV_FOLDER = r"mypath"
AUDIO_RECORDINGS_FOLDER = r"mypath"


def convert_wav_to_m4a():
    if not os.path.exists(AUDIO_RECORDINGS_FOLDER):
        os.makedirs(AUDIO_RECORDINGS_FOLDER, exist_ok=True)

    for file_name in os.listdir(RAW_WAV_FOLDER):
        if file_name.endswith(".wav"):
            wav_file_path = os.path.join(RAW_WAV_FOLDER, file_name)

            try:
                print(f"Processing file: {wav_file_path}")
                audio = AudioSegment.from_wav(wav_file_path)

                base_name = os.path.splitext(file_name)[0]
                m4a_file_name = f"{base_name}_{int(time.time())}.m4a"
                m4a_file_path = os.path.join(AUDIO_RECORDINGS_FOLDER, m4a_file_name)

                audio.export(m4a_file_path, format="mp4")
                print(f"Converted and saved: {m4a_file_path}")

                os.remove(wav_file_path)
                print(f"Deleted original WAV file: {wav_file_path}")

            except Exception as e:
                print(f"Error processing file {wav_file_path}: {e}")


if __name__ == "__main__":
    convert_wav_to_m4a()

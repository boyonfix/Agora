import os
import time
from pydub import AudioSegment

# Paths to folders
RAW_WAV_FOLDER = r"C:\Users\relle\OneDrive\Desktop\Agora\Raw_Wav"
AUDIO_RECORDINGS_FOLDER = r"C:\Users\relle\OneDrive\Desktop\Agora\Audio_Recordings"


def convert_wav_to_m4a():
    """
    Convert all WAV files in the Raw_Wav folder to M4A and save in the Audio_Recordings folder.
    Deletes the original WAV file after conversion.
    """
    if not os.path.exists(AUDIO_RECORDINGS_FOLDER):
        os.makedirs(AUDIO_RECORDINGS_FOLDER, exist_ok=True)

    for file_name in os.listdir(RAW_WAV_FOLDER):
        if file_name.endswith(".wav"):
            wav_file_path = os.path.join(RAW_WAV_FOLDER, file_name)

            try:
                # Load WAV file
                print(f"Processing file: {wav_file_path}")
                audio = AudioSegment.from_wav(wav_file_path)

                # Generate unique name for M4A file
                base_name = os.path.splitext(file_name)[0]
                m4a_file_name = f"{base_name}_{int(time.time())}.m4a"
                m4a_file_path = os.path.join(AUDIO_RECORDINGS_FOLDER, m4a_file_name)

                # Export to M4A
                audio.export(m4a_file_path, format="mp4")
                print(f"Converted and saved: {m4a_file_path}")

                # Delete original WAV file
                os.remove(wav_file_path)
                print(f"Deleted original WAV file: {wav_file_path}")

            except Exception as e:
                print(f"Error processing file {wav_file_path}: {e}")


# Call the conversion function
if __name__ == "__main__":
    convert_wav_to_m4a()
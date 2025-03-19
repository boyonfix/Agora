The files function within Agoras insfrastructure in the following way:

Recording Bridge1.0.py:
Automates the conversion of audio files from WAV to M4A format. It processes raw audio recordings stored in a designated folder and saves the converted files in an organized directory, facilitating streamlined management and further processing.

Recording.py:
Handles the processing of audio files by transcribing recorded speech to text, generating semantic embeddings for categorization, and assigning or creating meaningful categories based on content. This script interfaces directly with a SQLite database to store transcriptions, embeddings, and file paths systematically.

Playback Bridge 2.0.py:
Communicates with Agoras arduino to allow hardware connecotin to playback functionalities.

Playback.py
Provides enhanced playback features including detailed track navigation (forward/backward, fast-forward/rewind) and integrated recording functionality (remix and standard recordings). Users can pause playback to insert new recordings or remixes directly into audio tracks, enriching interactive audio experiences.

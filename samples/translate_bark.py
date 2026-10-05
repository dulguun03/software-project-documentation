"""Submit the included synthetic WAV fixture to the bark-translation sandbox.
The returned meaning is a deterministic demonstration, not real audio inference.
"""
from pathlib import Path
from client import multipart_file, post

audio_path = Path(__file__).resolve().parents[1] / "assets" / "einstein-bark.wav"
audio_body, audio_content_type = multipart_file(
    "audio", audio_path, "audio/wav", {"pet_id": "corgi_98231"})
post("/audio/translate-bark", body=audio_body, content_type=audio_content_type)

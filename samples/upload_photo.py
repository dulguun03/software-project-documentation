"""Upload the included Einstein image fixture as multipart form data.
Run server.py first; this sample uses its documented sandbox token.
"""
from pathlib import Path
from client import multipart_file, post

photo_path = Path(__file__).resolve().parents[1] / "assets" / "einstein.png"
photo_body, photo_content_type = multipart_file(
    "photo", photo_path, "image/png", {"pet_id": "corgi_98231"})
post("/pets/upload-photo", body=photo_body, content_type=photo_content_type)

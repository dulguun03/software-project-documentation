"""Shared transport; token is a public credential for this local sandbox only."""
import json
import os
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8080/v1")
AUTH_TOKEN = os.environ.get("API_AUTH_TOKEN", "sprint05-local-sandbox")

def post(path, payload=None, *, body=None, content_type="application/json"):
    request_body = body if body is not None else json.dumps(payload).encode("utf-8")
    request = Request(BASE_URL + path, data=request_body, method="POST", headers={
        "Authorization": "Bearer " + AUTH_TOKEN, "Content-Type": content_type})
    with urlopen(request, timeout=10) as response:
        response_body = json.load(response)
        print(json.dumps({"http_status": response.status, "body": response_body}, ensure_ascii=False))
        return response_body

def multipart_file(field_name, file_path, media_type, fields):
    boundary = "Sprint05MultipartBoundary91"
    parts = []
    for name, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"\r\nContent-Type: {media_type}\r\n\r\n'.encode())
    parts.extend([file_path.read_bytes(), f"\r\n--{boundary}--\r\n".encode()])
    return b"".join(parts), "multipart/form-data; boundary=" + boundary

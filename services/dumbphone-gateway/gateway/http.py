"""Tiny stdlib HTTP/JSON client so the gateway has zero dependencies."""

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional


class HttpError(Exception):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body[:200]}")
        self.status = status
        self.body = body


def request_json(
    method: str,
    url: str,
    *,
    json_body=None,
    form: Optional[dict] = None,
    headers: Optional[dict] = None,
    basic_auth: Optional[tuple] = None,
    timeout: float = 15,
):
    hdrs = {"Accept": "application/json", **(headers or {})}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode()
        hdrs["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    if basic_auth:
        token = base64.b64encode(f"{basic_auth[0]}:{basic_auth[1]}".encode()).decode()
        hdrs["Authorization"] = f"Basic {token}"

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode() or "null"
    except urllib.error.HTTPError as e:
        raise HttpError(e.code, e.read().decode(errors="replace")) from None
    return json.loads(body)

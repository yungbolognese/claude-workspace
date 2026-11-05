"""HTTP server for Twilio webhooks + background push-notification poller.

Routes (point your Twilio number at these):
    POST /sms          Messaging webhook ("A message comes in")
    POST /voice        Voice webhook ("A call comes in")
    POST /voice/input  Gather callback (used internally by the IVR)
    GET  /health       Liveness check
"""

import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Tuple

from .app import App
from .channels import twilio as tw
from .models import Inbound

log = logging.getLogger(__name__)

XML = "text/xml; charset=utf-8"
TEXT = "text/plain; charset=utf-8"


def handle_request(app: App, method: str, path: str, headers: Dict[str, str], body: bytes) -> Tuple[int, str, str]:
    """Pure request handler (no sockets) so it can be unit-tested."""
    route = path.split("?", 1)[0]
    if method == "GET" and route == "/health":
        return 200, TEXT, "ok"
    if method != "POST" or route not in ("/sms", "/voice", "/voice/input"):
        return 404, TEXT, "not found"

    params = tw.parse_form(body)
    if app.config.validate_signatures:
        url = app.config.public_base_url.rstrip("/") + path
        signature = headers.get("x-twilio-signature", "")
        if not tw.validate_signature(app.config.twilio_auth_token, url, params, signature):
            log.warning("rejected request with bad Twilio signature for %s", path)
            return 403, TEXT, "invalid signature"

    phone = params.get("From", "")
    if not phone:
        return 400, TEXT, "missing From"

    if route == "/sms":
        replies = app.gateway.handle(Inbound(phone=phone, text=params.get("Body", ""), channel="sms"))
        return 200, XML, tw.response(*(tw.message(r) for r in replies))
    if route == "/voice":
        return 200, XML, app.voice.incoming(phone)
    return 200, XML, app.voice.handle_input(phone, params.get("Digits", ""), params.get("SpeechResult", ""))


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        def _serve(self, method):
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""
            headers = {k.lower(): v for k, v in self.headers.items()}
            try:
                status, ctype, out = handle_request(app, method, self.path, headers, body)
            except Exception:
                log.exception("unhandled error")
                status, ctype, out = 500, TEXT, "error"
            data = out.encode()
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self._serve("GET")

        def do_POST(self):
            self._serve("POST")

        def log_message(self, fmt, *args):  # keep phone numbers out of stderr
            log.debug("%s - %s", self.address_string(), fmt % args)

    return Handler


def run_poller(app: App, stop: threading.Event) -> None:
    """Push ride status changes (driver assigned, arriving, ...) as outbound SMS."""
    while not stop.wait(app.config.poll_interval_seconds):
        for phone, text in app.gateway.poll_updates():
            try:
                app.sender.send(phone, text)
            except Exception:
                log.exception("failed to send push notification")


def check_config(app: App) -> None:
    cfg = app.config
    if cfg.validate_signatures and not (cfg.twilio_auth_token and cfg.public_base_url):
        raise SystemExit(
            "Signature validation is on but DPG_TWILIO_AUTH_TOKEN or DPG_PUBLIC_BASE_URL is missing.\n"
            "Set them, or set DPG_VALIDATE_SIGNATURES=0 for local testing only."
        )


def serve(app: App) -> None:
    check_config(app)
    stop = threading.Event()
    threading.Thread(target=run_poller, args=(app, stop), daemon=True, name="poller").start()
    server = ThreadingHTTPServer((app.config.host, app.config.port), make_handler(app))
    log.info("dumbphone gateway listening on http://%s:%d", app.config.host, app.config.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()

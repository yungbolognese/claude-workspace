"""Configuration, read from DPG_* environment variables.

Every field below maps to an environment variable named DPG_<FIELD_NAME_UPPER>,
e.g. ``ride_provider`` -> ``DPG_RIDE_PROVIDER``. See ``.env.example``.
"""

import os
from dataclasses import dataclass, fields


def _cast(raw: str, default):
    if isinstance(default, bool):
        return raw.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(default, int):
        return int(raw)
    if isinstance(default, float):
        return float(raw)
    return raw


@dataclass
class Config:
    # Storage / server
    db_path: str = "data/gateway.db"
    host: str = "127.0.0.1"
    port: int = 8080
    # The URL Twilio uses to reach this server (needed to validate signatures),
    # e.g. https://mac-mini.your-tailnet.ts.net
    public_base_url: str = ""

    # Users
    default_country_code: str = "1"
    allow_open_signup: bool = False  # False = only numbers added via admin CLI
    log_messages: bool = False  # store message bodies in SQLite (privacy: off)

    # Twilio (SMS + voice)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    validate_signatures: bool = True

    # Rideshare
    ride_provider: str = "mock"  # mock | uber_guest
    mock_speed: float = 1.0  # >1 makes the mock ride timeline run faster
    quote_ttl_seconds: int = 300
    poll_interval_seconds: int = 30

    # Geocoding (turning "123 Main St" into coordinates)
    geocoder: str = "none"  # none | nominatim
    geocoder_countries: str = ""  # e.g. "us" to bias Nominatim results
    geocoder_user_agent: str = "dumbphone-gateway/0.1"

    # Abuse protection
    rate_limit_count: int = 30
    rate_limit_window_seconds: int = 600
    max_pin_attempts: int = 3

    # Optional free-text understanding via local Ollama
    llm_fallback: bool = False
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"

    # Uber for Business Guest Rides
    uber_client_id: str = ""
    uber_client_secret: str = ""
    uber_scope: str = "guests.trips"  # confirm against your app's dashboard
    uber_sandbox: bool = True
    uber_sandbox_run_id: str = ""

    @classmethod
    def from_env(cls, environ=None) -> "Config":
        environ = os.environ if environ is None else environ
        cfg = cls()
        for f in fields(cls):
            key = "DPG_" + f.name.upper()
            if key in environ:
                setattr(cfg, f.name, _cast(environ[key], getattr(cfg, f.name)))
        return cfg

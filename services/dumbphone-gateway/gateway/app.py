"""Wire config -> store, providers, services, gateway, channels."""

import time
from dataclasses import dataclass
from typing import Callable, Optional

from .channels.twilio import ConsoleSender, Sender, TwilioSender
from .channels.voice import VoiceIVR
from .config import Config
from .geocode import Geocoder, build_geocoder
from .llm import OllamaRewriter
from .router import Gateway
from .services.places import PlacesService
from .services.ride_providers import RideProvider, build_provider
from .services.rideshare import RideshareService
from .store import Store


@dataclass
class App:
    config: Config
    store: Store
    gateway: Gateway
    voice: VoiceIVR
    sender: Sender


def build_app(
    config: Config,
    *,
    clock: Callable[[], float] = time.time,
    store: Optional[Store] = None,
    provider: Optional[RideProvider] = None,
    geocoder: Optional[Geocoder] = None,
    sender: Optional[Sender] = None,
) -> App:
    store = store or Store(config.db_path, clock=clock)
    geocoder = geocoder or build_geocoder(config)
    provider = provider or build_provider(config, clock=clock)
    services = [
        RideshareService(provider, geocoder, store, quote_ttl=config.quote_ttl_seconds,
                         max_pin_attempts=config.max_pin_attempts),
        PlacesService(geocoder),
    ]
    rewriter = OllamaRewriter(config.ollama_url, config.ollama_model) if config.llm_fallback else None
    gateway = Gateway(store, services, config, rewriter=rewriter, clock=clock)
    if sender is None:
        if config.twilio_account_sid and config.twilio_auth_token and config.twilio_from_number:
            sender = TwilioSender(config.twilio_account_sid, config.twilio_auth_token, config.twilio_from_number)
        else:
            sender = ConsoleSender()
    return App(config, store, gateway, VoiceIVR(gateway), sender)

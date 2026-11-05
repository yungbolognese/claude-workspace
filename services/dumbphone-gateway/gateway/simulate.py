"""Text the gateway from your terminal, no Twilio needed.

    python -m gateway.simulate            # SMS mode
    python -m gateway.simulate --pin 1234 # require a PIN to confirm bookings

Uses an in-memory database and the mock ride provider running 10x faster, with
HOME and WORK pre-saved. Push notifications print as [push] lines.
"""

import argparse
import threading

from .app import build_app
from .config import Config
from .models import Inbound, Place, hash_pin
from .server import run_poller

PHONE = "+15550100000"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m gateway.simulate")
    ap.add_argument("--pin", help="require this PIN to confirm bookings")
    ap.add_argument("--speed", type=float, default=10.0, help="mock ride speed multiplier")
    args = ap.parse_args(argv)

    cfg = Config.from_env()
    cfg.db_path = ":memory:"
    cfg.ride_provider = "mock"
    cfg.mock_speed = args.speed
    cfg.poll_interval_seconds = 2
    cfg.twilio_account_sid = ""  # never send real SMS from the simulator
    app = build_app(cfg)
    app.store.add_user(PHONE, "Sim User", hash_pin(args.pin) if args.pin else None)
    app.store.save_place(PHONE, Place(name="home", address="742 Evergreen Terrace"))
    app.store.save_place(PHONE, Place(name="work", address="100 Industrial Way"))

    stop = threading.Event()
    threading.Thread(target=run_poller, args=(app, stop), daemon=True).start()
    print(f"Simulating SMS from {PHONE}. Saved places: HOME, WORK. Try: RIDE home   (Ctrl-D to quit)")
    try:
        while True:
            text = input("\n> ")
            for reply in app.gateway.handle(Inbound(PHONE, text)):
                print(f"< {reply}  [{len(reply)} chars]")
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        stop.set()


if __name__ == "__main__":
    main()

"""Manage who can use the gateway.

    python -m gateway.admin add-user +15551234567 --name "Ann Lee" --pin 1234
    python -m gateway.admin list-users
    python -m gateway.admin add-place +15551234567 home "123 Main St, Springfield, IL"
    python -m gateway.admin remove-user +15551234567
"""

import argparse

from .config import Config
from .geocode import build_geocoder
from .models import hash_pin, normalize_phone
from .store import Store


def main(argv=None):
    cfg = Config.from_env()
    p = argparse.ArgumentParser(prog="python -m gateway.admin")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add-user", help="add or update a user")
    a.add_argument("phone")
    a.add_argument("--name", default="", help="full name (rideshare drivers see the first name)")
    a.add_argument("--pin", help="4-6 digit PIN required to confirm bookings (protects against caller-ID spoofing)")

    sub.add_parser("list-users")

    r = sub.add_parser("remove-user", help="delete a user and all their data")
    r.add_argument("phone")

    pl = sub.add_parser("add-place", help="save a place for a user")
    pl.add_argument("phone")
    pl.add_argument("name")
    pl.add_argument("address")

    args = p.parse_args(argv)
    store = Store(cfg.db_path)

    if args.cmd == "add-user":
        phone = normalize_phone(args.phone, cfg.default_country_code)
        store.add_user(phone, args.name, hash_pin(args.pin) if args.pin else None)
        print(f"added {phone}" + (" (PIN set)" if args.pin else ""))
    elif args.cmd == "list-users":
        for u in store.list_users():
            places = ", ".join(pl.name for pl in store.list_places(u.phone)) or "-"
            print(f"{u.phone}  {u.name or '-':20}  pin={'yes' if u.pin_hash else 'no '}  places={places}")
    elif args.cmd == "remove-user":
        phone = normalize_phone(args.phone, cfg.default_country_code)
        print("removed" if store.remove_user(phone) else "no such user")
    elif args.cmd == "add-place":
        phone = normalize_phone(args.phone, cfg.default_country_code)
        if store.get_user(phone) is None:
            raise SystemExit(f"{phone} is not a user; run add-user first")
        place = build_geocoder(cfg).geocode(args.address)
        if place is None:
            raise SystemExit("address not found")
        place.name = args.name.lower()
        store.save_place(phone, place)
        print(f"saved {place.name.upper()} = {place.address}" + (f" ({place.lat:.5f}, {place.lng:.5f})" if place.has_coords else ""))


if __name__ == "__main__":
    main()

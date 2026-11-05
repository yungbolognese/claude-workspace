"""python -m gateway  — run the webhook server."""

import logging

from .app import build_app
from .config import Config
from .server import serve


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    serve(build_app(Config.from_env()))


if __name__ == "__main__":
    main()

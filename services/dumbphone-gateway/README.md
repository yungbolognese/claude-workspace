# Dumbphone Gateway

Use smartphone-only services from a basic phone. Every phone can **text** and **call**, so the gateway turns SMS messages and phone calls into API calls and sends the results back as texts or speech.

The first service is **rideshare**: text `RIDE home` and a car comes.

```
 ┌────────────┐  SMS / call   ┌─────────┐  webhook  ┌───────────────────────── Mac mini ──┐
 │ dumb phone │ ────────────▶ │ Twilio  │ ────────▶ │ server.py ─▶ router.py ─▶ services/ │
 │            │ ◀──────────── │ number  │ ◀──────── │  (SMS/IVR)   (parse,     ├ rideshare ─▶ Uber / mock
 └────────────┘  replies +    └─────────┘  TwiML /  │              sessions,   └ places    │
                 push texts                REST     │              PIN, limits)            │
                                                    │ poller ─▶ status changes ─▶ push SMS │
                                                    └──────────────────────────────────────┘
```

- **No dependencies:** Python 3.9+ standard library only. State lives in SQLite.
- **Channel-agnostic core:** SMS and voice both become `Inbound(phone, text)`, so a new service works on both.
- **Pluggable services and providers:** rideshare doesn't know which company is driving.

## Try it in 30 seconds (no accounts needed)

```bash
cd services/dumbphone-gateway
python3 -m gateway.simulate
```

```
> RIDE home
< Where should the driver pick you up? Reply with an address or saved place. Reply NO to stop.
> 100 Industrial Way
< Standard from 100 Industrial Way to HOME: $23-27, pickup ~4 min. Reply YES to book, NO to cancel.
> YES
< Booked! Finding you a driver... Text STATUS for updates, CANCEL to cancel.
[push] to +15550100000: Sam is coming in a gray Toyota Camry, plate 7ABC123, ~2 min away.
```

Run the tests with `python3 -m unittest discover -s tests -t .`

## Commands

| Text | What it does |
|------|--------------|
| `RIDE home` | Ride to a saved place or address. The gateway then asks where to pick you up |
| `RIDE from work to home` | Pickup and drop-off in one text (`RIDE 5 Oak St > airport` also works) |
| `RIDE` | Asks for the destination, then the pickup |
| `YES` / `YES 1234` | Book the quoted ride (add your PIN if one is set) |
| `NO` | Abandon the current question or quote |
| `STATUS` | Driver, car, plate and ETA |
| `CANCEL` | Cancel a quote or an active ride |
| `SAVE clinic 12 Elm St, Springfield IL` | Save a place so you never type that address again |
| `PLACES` / `FORGET clinic` | List or delete saved places |
| `MENU` | Command list |

Synonyms: `CAB`, `TAXI`, `CAR`, `UBER` and `LYFT` all mean `RIDE`. Commands are case-insensitive. Addresses keep their case.

**Calling instead of texting:** press 1 for a ride home, 2 for status, 3 to cancel, or say a destination ("the airport"). Addresses are spoken, and you press 1 or 2 to confirm. Users with a PIN type it and press #.

**Free text (optional):** with `DPG_LLM_FALLBACK=1`, messages that don't match the grammar ("can u get me a car home") go to your local Ollama, which rewrites them into a command. The model can only produce `RIDE`, `STATUS`, `PLACES` or `MENU`. It can never confirm, cancel or delete anything, and message text never leaves your machine.

## Going live

### 1. Get a phone number
1. Create a [Twilio](https://www.twilio.com) account and buy a local number with SMS and voice. Other providers (Telnyx, Plivo, Vonage) also work, but you'd need to add a channel adapter.
2. **US numbers:** application-to-person SMS from a 10-digit number needs **A2P 10DLC registration** (brand plus campaign) before carriers deliver it. Start this early, because approval takes days. A toll-free number with toll-free verification is the alternative.

### 2. Expose the server
Twilio must reach your Mac mini over HTTPS. Pick one:
- **Tailscale Funnel** (fits this workspace): `tailscale funnel 8080` gives you `https://<machine>.<tailnet>.ts.net`
- Cloudflare Tunnel, or ngrok for quick tests

### 3. Configure and run
```bash
cp .env.example .env    # fill in values; .env is gitignored
set -a; source .env; set +a

python3 -m gateway.admin add-user +15551234567 --name "Ann Lee" --pin 4821
python3 -m gateway.admin add-place +15551234567 home "742 Evergreen Terrace, Springfield IL"

python3 -m gateway      # listens on DPG_HOST:DPG_PORT
```
In the Twilio console, set your number's webhooks:
- *A message comes in* → `POST https://<public-url>/sms`
- *A call comes in* → `POST https://<public-url>/voice`

### 4. Pick a ride provider

| Provider | Status | Notes |
|---|---|---|
| `mock` | ✅ Working | Simulated driver for development and demos |
| `uber_guest` | ⚠️ Written, **not verified against live API** | [Uber for Business Guest Rides](https://developer.uber.com/docs/guest-rides). Needs an approved Uber for Business account. Rides are billed to that account, not the rider. Test in the sandbox (`DPG_UBER_SANDBOX=1`) and compare response shapes first. Uber may also text the rider directly, so they could get duplicate updates |
| Lyft | Not built | Lyft's public ride-request API is closed. The business options are concierge-style programs that need a partnership |
| Local taxi | Idea | A `TAXI` command that bridges the call to a local dispatcher needs no API access. This is often the most practical option in smaller towns |

**Honest constraint:** the big rideshare companies no longer let arbitrary apps book rides on a person's own account. The workable route is a business account that books *guest* rides and pays for them. That suits a family member, care organization or employer paying for someone's rides. It does not suit a public service where strangers bill their own accounts.

`uber_guest` needs coordinates, so set `DPG_GEOCODER=nominatim`. Saved places are geocoded once when you save them, which is the main reason to encourage `SAVE`.

## Security model

Dumb phones can't do app logins, so the design assumes SMS and caller ID are weak identity signals.

| Risk | Mitigation |
|---|---|
| Strangers using your paid account | Allowlist: only numbers added with `gateway.admin` can use it (`DPG_ALLOW_OPEN_SIGNUP=0`) |
| **Caller-ID / SMS spoofing** | Optional per-user **PIN** (stored as a salted PBKDF2 hash) is required to confirm bookings. 3 wrong tries kill the quote |
| Forged webhooks | Every request's `X-Twilio-Signature` is validated. The server refuses to start without the auth token unless you explicitly disable validation |
| Accidental bookings | Nothing is booked without an explicit `YES` after a price quote. Quotes expire (5 min), and a double `YES` can't double-book |
| Reply loops with other bots / floods | Per-number rate limit (30 msgs / 10 min) and silent drop |
| LLM misreading a message | The LLM can't produce `YES`, `CANCEL` or `FORGET` |
| Privacy | Message bodies are **not** stored (`DPG_LOG_MESSAGES=0`). Everything stays in local SQLite. Ollama runs on-device. HTTP access logs are suppressed |

Not handled yet: SIM-swap detection, encrypting the SQLite file at rest, and spend caps per user.

## Adding a service

1. Subclass `Service` in `gateway/services/` and declare the `commands` it owns plus `help_lines`.
2. Add parser rules for new keywords in `gateway/parser.py`.
3. For multi-step flows, use `ctx.set_session(...)`. YES/NO/free-text replies are routed back to your `resume()`.
4. For async updates, return `(phone, text)` pairs from `poll_updates()`.
5. Register it in `gateway/app.py`. It works over SMS and voice automatically.

Candidate next services: transit arrivals (GTFS-realtime), turn-by-turn directions as a text list, 2FA code relay, grocery/pharmacy delivery status, and weather or alerts.

## Layout

```
gateway/
  app.py            wiring (config → store → providers → services → router)
  server.py         HTTP webhooks + push-notification poller
  router.py         auth, rate limiting, sessions, dispatch, LLM fallback guard
  parser.py         command grammar
  store.py          SQLite: users, places, sessions, rides
  channels/twilio.py  signature validation, TwiML, outbound SMS
  channels/voice.py   IVR (DTMF + speech → text commands)
  services/rideshare.py, ride_providers.py, places.py
  geocode.py, llm.py, admin.py, simulate.py
tests/              41 unit tests, stdlib unittest
```

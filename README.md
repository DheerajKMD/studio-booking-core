# Studio: booking core for boutique fitness studios

Django 5 + Django Ninja + PostgreSQL. Studios sell credit packs, members spend credits to book classes, with cancellation rules and a waitlist.

## Run it

Requires Docker.

```bash
docker compose up --build          # start the stack at http://localhost:8000
docker compose exec web python manage.py seed_demo   # demo users (second terminal)
docker compose run --rm web pytest # run the tests
```

API docs: http://localhost:8000/api/docs (OpenAPI: `/api/openapi.json`, also exported to `docs/openapi.json`).

Demo users (password `pass1234`): `meera` (staff), `arjun`, `divya`, `rahul` (members).

## Linters and types

```bash
docker compose run --rm web sh -c "ruff check . && ruff format --check . && mypy ."
```

CI (`.github/workflows/ci.yml`) runs ruff, mypy (strict) and pytest on every push.

## Architecture

```
apps/
  accounts/   users, roles, token auth, permissions
  studios/    studios, classes, browse with spots available
  credits/    packs, append-only ledger, FEFO spending, balances
  bookings/   bookings, cancellation policy, waitlist
  common/     clock, domain errors, idempotency
```

Each app separates `api.py` (thin Ninja routers), `services` (all writes, in transactions) and `selectors` (reads). Dependencies point one way: bookings -> credits/studios -> accounts/common.

Patterns used:
- **Service layer + selectors**: keeps HTTP thin and business rules testable.
- **Strategy** (`credits/spending.py`): FEFO spending behind an interface, so the policy can change without touching booking code.
- **Append-only ledger**: gives the audit trail and "balance as of time T" directly.
- **Policy object** (`cancellation_policy.py`): timezone/cutoff logic isolated and unit tested.
- **Injectable clock**: tests control time without patching globals.
- **Idempotency helper**: written once, reusable by any endpoint.

Concurrency: the class row is locked with `select_for_update` in booking, cancelling, joining and promotion (always class first), so a class never confirms more bookings than spots. Packs are locked while spending.

## Main flow

1. `POST /api/auth/login` as `meera` (staff), authorize with the token.
2. `POST /api/studios/` then `POST /api/studios/{id}/classes`.
3. `POST /api/credits/members/{id}/packs` to grant credits.
4. Members log in and `POST /api/bookings/classes/{id}` (optional `Idempotency-Key` header).
5. When full, `POST /api/bookings/classes/{id}/waitlist`.
6. `POST /api/bookings/{id}/cancel`: refunded before the cutoff (studio local time), forfeited after; the first affordable waitlisted member is promoted.
7. `GET /api/credits/members/{id}/balance` (add `?as_of=`) and `/movements` show the ledger.

## Decisions and scope

See `docs/DECISIONS.md` for rules the brief left open and what was left out.
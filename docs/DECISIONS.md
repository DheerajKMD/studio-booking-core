# Design decisions

Rules the brief left open, and the choice made for each.

## Ledger
- Append-only `LedgerEntry` rows (signed amount, one row per pack touched). Updates and deletes raise an error.
- A pack's remaining credits are the sum of its entries. There is no stored "remaining" column that could drift.
- Expiry is not a ledger movement. Credits stop being spendable after `expires_at`.
- Balance as of time T = entries with `created_at <= T` on packs not yet expired at T.
- Forfeits write no ledger entry: the original charge is already the outflow, so a second negative entry would deduct twice.

## Spending
- FEFO: the pack expiring soonest is spent first, ties broken by id. Implemented as a swappable strategy.
- Packs are row-locked while spending, so one member cannot spend the same credits twice concurrently.

## Booking and concurrency
- The class row is locked (`select_for_update`) in booking, cancelling, joining the waitlist and promotion, always class first. This prevents overbooking and deadlocks.
- A partial unique constraint allows one confirmed booking per member per class.
- Booking a class that has already started is rejected.

## Cancellation
- Cutoff = class start minus the studio's cutoff hours, computed in the studio's timezone. Cancelling at or before the cutoff refunds fully.
- A late cancel forfeits the credits but still frees the spot.
- A repeat cancel returns the booking unchanged and refunds nothing. The refund service also checks for an existing refund.
- Refunds return to the original packs. If a pack has expired, the credits are restored in the ledger but cannot be spent.
- A member cancelling someone else's booking gets 404, so ids do not leak. Staff can cancel any booking.
- Cancelling after the class has started is rejected.

## Waitlist
- Joining is allowed only when the class is full, and not if already booked or already waiting.
- Promotion runs after every cancellation, in the same transaction. Entries are tried in `joined_at`, then id, order.
- A member who cannot afford the class is skipped and keeps their place. Several freed spots are all filled.
- A waiting member who has since booked directly has their stale entry closed.

## Idempotency
- Keys are unique per member. Same key and same request returns the stored response.
- The same key with a different request returns 409.
- Only successful results are stored. A failed request rolls back, including its key, so it can be retried.

## Access
- Roles: staff and member. Members reach only their own bookings, credits and waitlist.
- There is no public signup. Staff create accounts through `POST /api/auth/users`. The first staff user comes from `seed_demo`.

## Other
- Classes have a `title` field, added so classes are browsable.
- Token auth: random tokens stored in the database, one per login, sent as a Bearer header.

## Left out
- Payments, notifications, attendance, instructors, recurring schedules, cash refunds, frontend.
- Token expiry and logout.
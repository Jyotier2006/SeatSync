# Demo Walkthrough

This walkthrough was executed end-to-end against a local instance of the API
(SQLite backend, migrations applied via Alembic, seeded with `scripts/seed.py`)
to verify the full booking lifecycle works as designed. Timestamps and IDs
below are from that run.

## 1. Register a second customer

```
POST /api/v1/auth/register
{"email":"second@seatsync.dev","password":"Second@12345","full_name":"Second Customer"}

201
{"access_token":"...","token_type":"bearer","user":{"id":"da90be0f-...","email":"second@seatsync.dev","role":"CUSTOMER"}}
```

## 2. Log in as the seeded demo customer

```
POST /api/v1/auth/login
{"email":"demo@seatsync.dev","password":"Demo@12345"}

200
{"access_token":"...","token_type":"bearer","user":{"id":"7c31c9bd-...","email":"demo@seatsync.dev","role":"CUSTOMER"}}
```

## 3. Browse movies and shows

```
GET /api/v1/movies
200
[{"title":"Concurrency: The Movie","language":"English","id":"4f299f61-..."}]

GET /api/v1/movies/4f299f61-.../shows
200
[{"show_id":"57065fa9-...","venue_name":"SeatSync Cinema","city":"Ahmedabad","screen_name":"Screen 1"}]
```

## 4. View seats for the show

```
GET /api/v1/shows/57065fa9-.../seats
200
[{"id":"ae8566db-...","row_label":"A","number":1,"category":"STANDARD","price":"250.00","status":"AVAILABLE"}, ...]
```

## 5. User 1 locks seat A1

```
POST /api/v1/seat-locks
Authorization: Bearer <user1_token>
{"show_id":"57065fa9-...","show_seat_ids":["ae8566db-..."]}

201
{"lock_token":"RRlhGF31Awr6sM1U0zM8N2QceT3U5rNqtODfp2q_5yI","expires_at":"2026-07-23T15:20:26.773293Z"}
```

## 6. User 2 attempts to lock the same seat

```
POST /api/v1/seat-locks
Authorization: Bearer <user2_token>
{"show_id":"57065fa9-...","show_seat_ids":["ae8566db-..."]}

409 Conflict
{"detail":"One or more selected seats are no longer available"}
```

Confirms the second, concurrent request is rejected — the seat's status
column is only flipped `AVAILABLE -> LOCKED` by a conditional `UPDATE ...
WHERE status = 'AVAILABLE'`, so only one of two racing requests can ever
match the row.

## 7. Create a booking from the lock

```
POST /api/v1/bookings
Authorization: Bearer <user1_token>
{"lock_token":"RRlhGF31Awr6sM1U0zM8N2QceT3U5rNqtODfp2q_5yI"}

201
{"id":"ec084e4b-...","booking_reference":"SS88DD9450","status":"PENDING_PAYMENT","total_amount":"250.00"}
```

## 8. Initiate payment (idempotent)

```
POST /api/v1/payments
{"booking_id":"ec084e4b-...","method":"CARD","idempotency_key":"demo-idem-key-001"}

201
{"id":"66761911-...","status":"PENDING","amount":"250.00"}
```

Retried the exact same request body (same `idempotency_key`) and received
the identical payment record back (`id":"66761911-..."`, unchanged) instead
of a second payment being created — confirms idempotency at the service
layer.

## 9. Confirm payment success

```
POST /api/v1/payments/66761911-.../mock-result
{"success":true,"gateway_reference":"gw-ref-001"}

200
{"id":"66761911-...","status":"SUCCESS","gateway_reference":"gw-ref-001"}
```

## 10. Verify booking confirmation

```
GET /api/v1/bookings/ec084e4b-...
200
{"status":"CONFIRMED","total_amount":"250.00"}
```

## 11. Cancel the booking

```
POST /api/v1/bookings/ec084e4b-.../cancel
200
{"status":"REFUNDED","total_amount":"250.00"}
```

## 12. Verify the seat was released back to inventory

```
GET /api/v1/shows/57065fa9-.../seats
200
[{"id":"ae8566db-...","status":"AVAILABLE"}, ...]
```

Seat A1 is `AVAILABLE` again after cancellation, and would be lockable by
another user.

## Test suite

```
pytest tests -v --ignore=tests/integration
8 passed, 16 warnings in 13.11s
```

`tests/integration/test_postgres_race.py` was not run in this pass — it
spins up real concurrent threads/processes against a live Postgres instance
to prove the lock holds under actual concurrency (not just sequential
requests as shown above), and needs `DATABASE_URL` pointed at Postgres via
`docker compose up`.

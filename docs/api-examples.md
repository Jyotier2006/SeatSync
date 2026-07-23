# API walkthrough

Set the base URL:

```bash
BASE=http://localhost:8000/api/v1
```

## 1. Login

```bash
TOKEN=$(curl -s -X POST "$BASE/auth/login"   -H 'Content-Type: application/json'   -d '{"email":"demo@seatsync.dev","password":"Demo@12345"}'   | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
```

## 2. Discover a show and seat

```bash
curl "$BASE/movies"
curl "$BASE/movies/<MOVIE_ID>/shows"
curl "$BASE/shows/<SHOW_ID>/seats"
```

## 3. Lock seats

```bash
curl -X POST "$BASE/seat-locks"   -H "Authorization: Bearer $TOKEN"   -H 'Content-Type: application/json'   -d '{"show_id":"<SHOW_ID>","show_seat_ids":["<SHOW_SEAT_ID>"]}'
```

## 4. Create booking

```bash
curl -X POST "$BASE/bookings"   -H "Authorization: Bearer $TOKEN"   -H 'Content-Type: application/json'   -d '{"lock_token":"<LOCK_TOKEN>"}'
```

## 5. Initiate and complete mock payment

```bash
curl -X POST "$BASE/payments"   -H "Authorization: Bearer $TOKEN"   -H 'Content-Type: application/json'   -d '{"booking_id":"<BOOKING_ID>","method":"UPI","idempotency_key":"unique-checkout-001"}'

curl -X POST "$BASE/payments/<PAYMENT_ID>/mock-result"   -H "Authorization: Bearer $TOKEN"   -H 'Content-Type: application/json'   -d '{"success":true,"gateway_reference":"demo-gateway-001"}'
```

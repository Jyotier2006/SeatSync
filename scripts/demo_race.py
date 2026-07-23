"""Demonstrate that exactly one concurrent request can lock a seat.

Run the API and seed data first, then execute:
    python scripts/demo_race.py
"""

import concurrent.futures
import os

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api/v1")


def login() -> str:
    response = httpx.post(
        f"{BASE_URL}/auth/login",
        json={"email": "demo@seatsync.dev", "password": "Demo@12345"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def main() -> None:
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    movies = httpx.get(f"{BASE_URL}/movies", timeout=10).json()
    shows = httpx.get(f"{BASE_URL}/movies/{movies[0]['id']}/shows", timeout=10).json()
    seats = httpx.get(f"{BASE_URL}/shows/{shows[0]['show_id']}/seats", timeout=10).json()
    seat_id = next(seat["id"] for seat in seats if seat["status"] == "AVAILABLE")

    def attempt(index: int):
        response = httpx.post(
            f"{BASE_URL}/seat-locks",
            headers=headers,
            json={"show_id": shows[0]["show_id"], "show_seat_ids": [seat_id]},
            timeout=10,
        )
        return index, response.status_code, response.json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(attempt, range(10)))

    for result in results:
        print(result)
    print("Successful locks:", sum(status == 201 for _, status, _ in results))


if __name__ == "__main__":
    main()

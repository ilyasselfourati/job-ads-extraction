"""Client for France Travail's "Offres d'emploi" API."""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
SCOPE = "api_offresdemploiv2 o2dsoffre"


def get_access_token() -> str:
    load_dotenv()
    client_id = os.environ["FRANCE_TRAVAIL_CLIENT_ID"]
    client_secret = os.environ["FRANCE_TRAVAIL_CLIENT_SECRET"]

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": SCOPE,
        },
        timeout=10,
    )
    response.raise_for_status()
    token: str = response.json()["access_token"]
    return token


SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"


def search_offers(access_token: str, keywords: str, range_start: int, range_end: int) -> list[dict[str, Any]]:
    response = requests.get(
        SEARCH_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "motsCles": keywords,
            "range": f"{range_start}-{range_end}",
            "sort": "1",
        },
        timeout=10,
    )
    response.raise_for_status()
    results: list[dict[str, Any]] = response.json().get("resultats", [])
    return results


REQUEST_DELAY_SECONDS = 0.15
RANGE_SIZE = 20


def load_existing_ids(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()

    ids = set()
    with output_path.open(encoding="utf-8") as f:
        for line in f:
            offer = json.loads(line)
            ids.add(offer["id"])
    return ids


def append_offers(output_path: Path, offers: list[dict[str, Any]], seen_ids: set[str]) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    new_count = 0
    with output_path.open("a", encoding="utf-8") as f:
        for offer in offers:
            if offer["id"] in seen_ids:
                continue
            f.write(json.dumps(offer, ensure_ascii=False) + "\n")
            seen_ids.add(offer["id"])
            new_count += 1
    return new_count


def collect(keywords: str, min_new_offers: int, output_path: Path, max_pages: int = 20) -> int:
    seen_ids = load_existing_ids(output_path)
    token = get_access_token()

    total_new = 0
    for page in range(max_pages):
        if total_new >= min_new_offers:
            break

        range_start = page * RANGE_SIZE
        range_end = range_start + RANGE_SIZE - 1
        offers = search_offers(token, keywords, range_start, range_end)
        if not offers:
            break

        total_new += append_offers(output_path, offers, seen_ids)
        time.sleep(REQUEST_DELAY_SECONDS)

    return total_new


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect raw job offers from the France Travail API.")
    parser.add_argument("--keywords", default="developpeur")
    parser.add_argument("--min-new-offers", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("data/raw/france_travail_offers.jsonl"))
    args = parser.parse_args()

    new_count = collect(args.keywords, args.min_new_offers, args.output)
    print(f"{new_count} new offers appended to {args.output}")


if __name__ == "__main__":
    main()

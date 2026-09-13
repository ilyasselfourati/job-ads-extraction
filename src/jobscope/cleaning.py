"""Cleaning and deduplication of raw job postings before annotation."""

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    without_tags = TAG_RE.sub("", text)
    return html.unescape(without_tags)


def normalize_whitespace(text: str) -> str:
    normalized_unicode = unicodedata.normalize("NFKC", text)
    collapsed = WHITESPACE_RE.sub(" ", normalized_unicode)
    return collapsed.strip()


def clean_text(text: str) -> str:
    return normalize_whitespace(strip_html(text))


def clean_corpus(input_path: Path, output_path: Path) -> tuple[int, int]:
    seen_descriptions: set[str] = set()
    total_read = 0
    kept_offers = []

    with input_path.open(encoding="utf-8") as f:
        for line in f:
            total_read += 1
            offer = json.loads(line)

            offer["intitule"] = clean_text(offer.get("intitule", "") or "")
            offer["description"] = clean_text(offer.get("description", "") or "")

            if offer["description"] in seen_descriptions:
                continue
            seen_descriptions.add(offer["description"])
            kept_offers.append(offer)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for offer in kept_offers:
            f.write(json.dumps(offer, ensure_ascii=False) + "\n")

    return total_read, len(kept_offers)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean and deduplicate raw job offers.")
    parser.add_argument("--input", type=Path, default=Path("data/raw/france_travail_offers.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/interim/france_travail_offers_clean.jsonl"))
    args = parser.parse_args()

    total_read, total_kept = clean_corpus(args.input, args.output)
    print(f"{total_read} offres lues, {total_kept} conservees apres nettoyage/dedup -> {args.output}")


if __name__ == "__main__":
    main()

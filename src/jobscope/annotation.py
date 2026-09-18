"""Export the cleaned corpus to a spreadsheet for manual annotation, and import it back."""

import argparse
import csv
import json
from pathlib import Path

LABEL_COLUMNS = [
    "seniority",
    "contract_type",
    "home_office_policy",
    "min_salary",
    "max_salary",
    "salary_period",
    "skills",
]
REFERENCE_COLUMNS = ["offer_id", "intitule", "description"]
ALL_COLUMNS = REFERENCE_COLUMNS + LABEL_COLUMNS


def export_for_annotation(input_path: Path, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    row_count = 0
    with input_path.open(encoding="utf-8") as f_in, output_path.open("w", encoding="utf-8-sig", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=ALL_COLUMNS)
        writer.writeheader()

        for line in f_in:
            offer = json.loads(line)
            writer.writerow(
                {
                    "offer_id": offer["id"],
                    "intitule": offer.get("intitule", ""),
                    "description": offer.get("description", ""),
                }
            )
            row_count += 1

    return row_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Export cleaned offers to a CSV for annotation in a spreadsheet.")
    parser.add_argument("--input", type=Path, default=Path("data/interim/france_travail_offers_clean.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/interim/annotation_sheet.csv"))
    args = parser.parse_args()

    row_count = export_for_annotation(args.input, args.output)
    print(f"{row_count} offres exportees vers {args.output}")


if __name__ == "__main__":
    main()

"""Build a traceable generic DTC fixture from an allow-listed code file.

The source database is never copied wholesale. Only requested generic English
definitions are exported, with provenance and a report for missing codes.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codes", type=Path, required=True)
    parser.add_argument("--source-db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()

    occurrences = [code.strip().upper() for code in args.codes.read_text().split()]
    unique_codes = sorted(set(occurrences))
    connection = sqlite3.connect(args.source_db)
    placeholders = ",".join("?" for _ in unique_codes)
    rows = connection.execute(
        f"SELECT code, description, type FROM dtc_definitions "
        f"WHERE is_generic = 1 AND locale = 'en' AND code IN ({placeholders}) "
        "ORDER BY code",
        unique_codes,
    ).fetchall()
    connection.close()

    definitions = [
        {"code": code, "description_en": description, "category": type}
        for code, description, type in rows
    ]
    found = {item["code"] for item in definitions}
    missing = sorted(set(unique_codes) - found)
    payload = {
        "schema_version": "1.0",
        "source": {
            "title": "Wal33D DTC Database — requested generic definitions",
            "publisher": "Waleed Judah (Wal33D)",
            "source_type": "open_source_dataset",
            "source_url": "https://github.com/Wal33D/dtc-database",
            "source_commit": args.source_commit,
            "license_type": "MIT",
            "language": "en",
            "trust_level": "community_open_data",
            "review_status": "unreviewed",
            "standard_claim": "Dataset describes its generic coverage as SAE J2012; not independently verified against the licensed current SAE J2012DA.",
        },
        "input_report": {
            "occurrences": len(occurrences),
            "unique_codes": len(unique_codes),
            "duplicates_removed": len(occurrences) - len(unique_codes),
            "matched": len(definitions),
            "missing": missing,
        },
        "definitions": definitions,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    payload["content_checksum_sha256"] = hashlib.sha256(canonical).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload["input_report"], ensure_ascii=False))
    if missing:
        raise SystemExit("Some requested codes have no verified generic definition")


if __name__ == "__main__":
    main()


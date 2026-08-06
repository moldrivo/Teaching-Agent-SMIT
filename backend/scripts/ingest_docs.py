"""Ingest local docs into the RAG store via the running API.

Usage (from the backend/ directory):
    python -m scripts.ingest_docs "docs/**/*.md" "README.md"
"""
import glob
import sys

import httpx

API_URL = "http://localhost:8000/api/ingest"


def main() -> None:
    patterns = sys.argv[1:]
    if not patterns:
        print("Usage: python -m scripts.ingest_docs 'docs/**/*.md' [more globs]")
        return

    documents = []
    for pattern in patterns:
        for path in glob.glob(pattern, recursive=True):
            try:
                with open(path, encoding="utf-8") as fh:
                    documents.append(fh.read())
                print(f"  + {path}")
            except OSError as exc:
                print(f"  - skipped {path}: {exc}")

    if not documents:
        print("No matching files found.")
        return

    response = httpx.post(
        API_URL,
        json={"documents": documents, "source": "local-docs"},
        timeout=120,
    )
    response.raise_for_status()
    print(f"Ingested {response.json()}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Acquire CC0 panorama JPEG previews from the frozen Zenodo record."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time
import requests

RECORD_ID = 1285800
ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "data/raw/drosophila_counterevidence_natural_scenes/previews"
MANIFEST_PATH = ROOT / "data/raw/drosophila_counterevidence_natural_scenes/source_manifest.json"


def digest(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(item):
    url = item["links"]["self"]
    target = DEST / item["key"]
    expected_md5 = item["checksum"].split(":", 1)[1]
    for attempt in range(9):
        try:
            if target.exists() and target.stat().st_size == item["size"] and digest(target, "md5") == expected_md5:
                return {"key": item["key"], "id": item["id"], "url": url,
                        "bytes": target.stat().st_size, "zenodo_md5": expected_md5,
                        "local_sha256": digest(target, "sha256")}
            response = requests.get(url, timeout=(20, 120))
            if response.status_code == 429:
                wait = min(60, 2 ** min(attempt + 1, 6))
                print(f"rate limited; retry {item['key']} in {wait}s", flush=True)
                time.sleep(wait)
                continue
            response.raise_for_status()
            payload = response.content
            if len(payload) != item["size"]:
                raise ValueError(f"size mismatch for {item['key']}")
            if hashlib.md5(payload).hexdigest() != expected_md5:
                raise ValueError(f"Zenodo MD5 mismatch for {item['key']}")
            target.write_bytes(payload)
            return {"key": item["key"], "id": item["id"], "url": url,
                    "bytes": len(payload), "zenodo_md5": expected_md5,
                    "local_sha256": digest(target, "sha256")}
        except Exception:
            if attempt == 8:
                raise
            time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(item["key"])


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    response = requests.get(f"https://zenodo.org/api/records/{RECORD_ID}", timeout=60)
    response.raise_for_status()
    record = response.json()
    files = sorted((f for f in record["files"] if f["key"].endswith(".preview.jpg")), key=lambda f: f["key"])
    done = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(fetch, item): item for item in files}
        for future in as_completed(jobs):
            done.append(future.result())
            if len(done) % 25 == 0 or len(done) == len(files):
                print(f"acquired {len(done)}/{len(files)} previews", flush=True)
    done.sort(key=lambda row: row["key"])
    manifest = {"doi": record["doi"], "record_id": RECORD_ID,
                "version": record["metadata"].get("version"),
                "title": record["metadata"].get("title"),
                "license": record["metadata"].get("license"),
                "creator": record["metadata"].get("creators"),
                "preview_count": len(done), "total_bytes": sum(row["bytes"] for row in done),
                "api_url": f"https://zenodo.org/api/records/{RECORD_ID}",
                "files": done}
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in ("doi", "version", "preview_count", "total_bytes")}, indent=2))


if __name__ == "__main__":
    main()

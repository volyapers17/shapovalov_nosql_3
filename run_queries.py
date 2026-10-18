#!/usr/bin/env python3
"""Run named Cypher statements through Neo4j 5 HTTP; save complete evidence."""
import argparse
import base64
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def execute(statement):
    password = os.environ.get("NEO4J_PASSWORD", "password123")
    token = base64.b64encode(f"neo4j:{password}".encode()).decode()
    body = {"statements": [{"statement": statement, "includeStats": True}]}
    request = urllib.request.Request(
        os.environ.get("NEO4J_HTTP", "http://127.0.0.1:7474") + "/db/neo4j/tx/commit",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Basic " + token},
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=3600) as response:
        result = json.load(response)
    if result["errors"]:
        raise RuntimeError(result["errors"])
    data = result["results"][0]
    records = [dict(zip(data["columns"], row["row"])) for row in data["data"]]
    for record in records:
        if record.get("failedBatches", 0) or record.get("failedOperations", 0):
            raise RuntimeError(record)
    return {"executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "seconds": round(time.perf_counter()-start, 4),
            "query": statement, "columns": data["columns"], "rows": records,
            "stats": data.get("stats", {})}


def statements(path):
    # Each @name block contains exactly one statement; semicolons inside strings
    # are not treated as delimiters.
    pieces = re.split(r"(?m)^// @name (\w+)\s*$", path.read_text(encoding="utf-8"))
    for i in range(1, len(pieces), 2):
        yield pieces[i], pieces[i+1].strip().removesuffix(";")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--only", nargs="+")
    parser.add_argument("--prefix", default="")
    args = parser.parse_args()
    for name, statement in statements(args.file):
        if args.only and name not in args.only:
            continue
        print(f"Running {name}...", flush=True)
        result = execute(statement)
        (ROOT / "results").mkdir(exist_ok=True)
        (ROOT / "results" / f"{args.prefix}{name}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  {result['seconds']}s; {len(result['rows'])} rows; {str(result['rows'][:2])[:500]}", flush=True)

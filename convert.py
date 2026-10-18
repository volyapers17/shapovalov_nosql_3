#!/usr/bin/env python3
"""MovieLens 1M ZIP -> validated UTF-8 CSV. Python standard library only."""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def convert(archive: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        # Read named members only: never blindly extract arbitrary ZIP paths.
        readme = z.read("ml-1m/README").decode("latin-1")
        print(readme)

        def rows(name, width):
            with z.open(f"ml-1m/{name}.dat") as raw:
                for line_number, line in enumerate(io.TextIOWrapper(raw, encoding="latin-1"), 1):
                    values = line.rstrip("\r\n").split("::")
                    if len(values) != width:
                        raise ValueError(f"{name}:{line_number}: expected {width} fields")
                    yield values

        def write(name, header, data):
            path = output / f"{name}.csv"
            temp = path.with_suffix(".csv.tmp")
            try:
                with temp.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(data)
                temp.replace(path)
            finally:
                temp.unlink(missing_ok=True)

        movies, users, genres = set(), set(), Counter()

        def movie_rows():
            for mid, title, raw_genres in rows("movies", 3):
                mid = int(mid)
                if mid in movies:
                    raise ValueError(f"duplicate movie {mid}")
                movies.add(mid)
                match = re.search(r"\((\d{4})\)$", title)
                if not match:
                    raise ValueError(f"missing year: {title}")
                names = raw_genres.split("|")
                if len(names) != len(set(names)):
                    raise ValueError(f"duplicate genres: {mid}")
                genres.update(names)
                yield mid, title, int(match[1]), raw_genres

        write("movies", ["movieId", "title", "year", "genres"], movie_rows())

        def user_rows():
            for uid, gender, age, occupation, _zip in rows("users", 5):
                uid, age, occupation = int(uid), int(age), int(occupation)
                if uid in users or gender not in {"M", "F"}:
                    raise ValueError(f"invalid user {uid}")
                if age not in {1, 18, 25, 35, 45, 50, 56} or not 0 <= occupation <= 20:
                    raise ValueError(f"invalid demographic codes {uid}")
                users.add(uid)
                yield uid, gender, age, occupation

        write("users", ["userId", "gender", "age", "occupation"], user_rows())
        pairs, rating_counts, user_counts = set(), Counter(), Counter()

        def rating_rows():
            for raw in rows("ratings", 4):
                uid, mid, rating, timestamp = map(int, raw)
                if uid not in users or mid not in movies:
                    raise ValueError(f"orphan rating {uid}/{mid}")
                if not 1 <= rating <= 5 or timestamp < 0 or (uid, mid) in pairs:
                    raise ValueError(f"invalid or duplicate rating {uid}/{mid}")
                pairs.add((uid, mid))
                rating_counts[rating] += 1
                user_counts[uid] += 1
                yield uid, mid, rating, timestamp

        write("ratings", ["userId", "movieId", "rating", "timestamp"], rating_rows())
    result = {
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "movies": len(movies), "users": len(users), "ratings": len(pairs),
        "genres": len(genres), "has_genre": sum(genres.values()),
        "genre_movie_counts": dict(sorted(genres.items())),
        "rating_distribution": dict(sorted(rating_counts.items())),
        "minimum_ratings_per_user": min((user_counts[uid] for uid in users), default=0),
        "duplicate_user_movie_pairs": 0,
        "orphan_ratings": 0,
        "csv_sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                       for name in ["movies.csv", "ratings.csv", "users.csv"]},
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "import")
    args = parser.parse_args()
    result = convert(args.archive, args.output)
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/conversion.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

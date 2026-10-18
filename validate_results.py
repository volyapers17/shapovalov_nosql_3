#!/usr/bin/env python3
"""Independent SQLite checks for ALL Q1–Q5 rows + path and import invariants."""
import csv
import json
import math
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def saved(name):
    return json.loads((ROOT / f"results/{name}.json").read_text())["rows"]


def main():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE movies(movieId INTEGER PRIMARY KEY,title TEXT,year INTEGER);
    CREATE TABLE genres(movieId INTEGER,genre TEXT,PRIMARY KEY(movieId,genre));
    CREATE TABLE ratings(userId INTEGER,movieId INTEGER,rating INTEGER,timestamp INTEGER,
                         PRIMARY KEY(userId,movieId));
    CREATE INDEX rating_movie ON ratings(movieId);
    """)
    with (ROOT/"import/movies.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            db.execute("INSERT INTO movies VALUES(?,?,?)",(int(r["movieId"]),r["title"],int(r["year"])))
            db.executemany("INSERT INTO genres VALUES(?,?)",
                           [(int(r["movieId"]),g) for g in r["genres"].split("|")])
    with (ROOT/"import/ratings.csv").open() as f:
        db.executemany("INSERT INTO ratings VALUES(?,?,?,?)",
                       (tuple(map(int,(r["userId"],r["movieId"],r["rating"],r["timestamp"])))
                        for r in csv.DictReader(f)))
    sql = {
        "q1_thrillers": """SELECT m.movieId,m.title,AVG(r.rating) AS averageRating,
        COUNT(*) AS ratingCount FROM movies m JOIN genres g USING(movieId)
        JOIN ratings r USING(movieId) WHERE g.genre='Thriller'
        GROUP BY m.movieId HAVING AVG(r.rating)>4
        ORDER BY averageRating DESC,ratingCount DESC,m.movieId""",
        "q2_five_star_users": """SELECT userId,COUNT(DISTINCT movieId) AS fiveStarMovies
        FROM ratings WHERE rating=5 GROUP BY userId HAVING COUNT(DISTINCT movieId)>50
        ORDER BY fiveStarMovies DESC,userId""",
        "q3_shared_favourites": """SELECT m.movieId,m.title,a.rating AS user1Rating,
        b.rating AS user2Rating FROM ratings a JOIN ratings b USING(movieId)
        JOIN movies m USING(movieId) WHERE a.userId=1 AND b.userId=2
        AND a.rating>=4 AND b.rating>=4 ORDER BY m.movieId""",
        "q4_genres": """SELECT g.genre,AVG(r.rating) AS averageRating,COUNT(*) AS ratingCount,
        COUNT(DISTINCT r.movieId) AS ratedMovies,
        sqrt(AVG(1.0*r.rating*r.rating)-AVG(r.rating)*AVG(r.rating)) AS ratingStdDev,
        AVG(CASE WHEN r.rating>=4 THEN 1.0 ELSE 0 END) AS highRatingShare,
        AVG(r.rating)>=4 AND COUNT(*)>=1000 AND
        AVG(CASE WHEN r.rating>=4 THEN 1.0 ELSE 0 END)>=0.70 AS consistentlyHigh
        FROM genres g JOIN ratings r USING(movieId) GROUP BY g.genre
        ORDER BY averageRating DESC,g.genre""",
        "q5_recommendations": (ROOT/"queries/recommendation.sql").read_text(),
    }
    db.create_function("sqrt",1,math.sqrt)
    checks = {}
    for name, statement in sql.items():
        expected = [dict(r) for r in db.execute(statement)]
        actual = saved(name)
        assert len(expected) == len(actual), name
        for exp, act in zip(expected, actual):
            assert exp.keys() == act.keys(), (name,exp,act)
            for key,value in exp.items():
                if isinstance(value,float):
                    assert math.isclose(value,act[key],rel_tol=1e-10,abs_tol=1e-10),(name,key)
                else:
                    assert value == act[key],(name,key,value,act[key])
        checks[name] = {"all_rows_match_sqlite":True,"rows":len(actual)}
    q6 = saved("q6_shortest_path")[0]
    assert q6["hops"] == 2 and len(q6["chain"]) == 3
    assert q6["chain"][0] == "User 1" and q6["chain"][-1] == "User 2"
    witness = db.execute("""SELECT m.title FROM ratings a JOIN ratings b USING(movieId)
      JOIN movies m USING(movieId) WHERE a.userId=1 AND b.userId=2 AND m.title=?""",
                         (q6["chain"][1],)).fetchone()
    assert witness
    checks["q6_shortest_path"] = {"real_shared_movie":True,"minimum_hops":2,
        "reason":"Distinct users in a bipartite User-Movie graph cannot be directly adjacent."}
    expected_counts = {"users":6040,"movies":3883,"genres":18,"ratings":1000209,"hasGenre":6408}
    assert saved("counts") == saved("repeat_counts") == [expected_counts]
    assert saved("duplicate_ratings") == [{"duplicatePairs":0}]
    assert saved("invalid_ratings") == [{"invalid":0}]
    sampled_weights = saved("similarity_sample_check")
    assert len(sampled_weights) == 20
    assert all(r["correct"] for r in sampled_weights)
    checks["import"] = {"full_dataset_counts":True,"idempotent":True,"duplicate_pairs":0}
    checks["derived_weights"] = {"twenty_pairs_verified_in_cypher":True}
    (ROOT/"results/validation.json").write_text(json.dumps(checks,indent=2)+"\n")
    print(json.dumps(checks,indent=2))


if __name__ == "__main__":
    main()

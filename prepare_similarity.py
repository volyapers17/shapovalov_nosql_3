#!/usr/bin/env python3
"""Exact co-rating counts using sparse integer matrix products (optional GDS).

B[u,m]=1 iff rating>=4. B.T@B counts common users, B@B.T common movies.
This avoids producing every two-hop path as a separate Cypher intermediate row.
"""
import csv
import json
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parent


def main():
    with (ROOT / "import/users.csv").open() as f:
        users = sorted(int(r["userId"]) for r in csv.DictReader(f))
    with (ROOT / "import/movies.csv").open(encoding="utf-8") as f:
        movies = sorted(int(r["movieId"]) for r in csv.DictReader(f))
    ui, mi = {v:i for i,v in enumerate(users)}, {v:i for i,v in enumerate(movies)}
    us, ms = [], []
    rating_counts = np.zeros(len(movies), dtype=np.int64)
    with (ROOT / "import/ratings.csv").open() as f:
        for r in csv.DictReader(f):
            m = mi[int(r["movieId"])]
            rating_counts[m] += 1
            if int(r["rating"]) >= 4:
                us.append(ui[int(r["userId"])])
                ms.append(m)
    b = sparse.csr_matrix((np.ones(len(us), dtype=np.int64), (us,ms)),
                          shape=(len(users),len(movies)))
    report = {"method":"exact sparse int64 products", "high_rating_threshold":4,
              "top_edges":50000, "numpy":np.__version__}
    for name, matrix, ids in [("co_rated", b.T@b, movies), ("similar", b@b.T, users)]:
        coo = sparse.triu(matrix, k=1).tocoo()
        valid = coo.data > 0
        if name == "co_rated":
            valid &= (rating_counts[coo.row] > 20) & (rating_counts[coo.col] > 20)
        a, c, w = coo.row[valid], coo.col[valid], coo.data[valid]
        # Same ORDER BY weight DESC, source business ID, target business ID.
        selected = np.lexsort((c,a,-w))[:50000]
        with (ROOT / f"import/{name}.csv").open("w",newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["source","target","weight","distance"])
            writer.writerows((ids[a[i]],ids[c[i]],int(w[i]),1.0/int(w[i])) for i in selected)
        report[name] = {"positive_candidate_pairs":len(w), "selected_pairs":len(selected),
                        "min_weight":int(w[selected].min()),"max_weight":int(w[selected].max())}
    (ROOT / "results/similarity_preparation.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()

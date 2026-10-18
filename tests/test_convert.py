import contextlib
import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from convert import convert


class ConversionTests(unittest.TestCase):
    def run_fixture(self, movies="1::Café, The (L'Associe)(1982)::Drama|Comedy\n",
                    ratings="1::1::5::100\n"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "test.zip"
            with zipfile.ZipFile(archive, "w") as z:
                for name, text in {
                    "README":"Test fixture only", "movies.dat":movies,
                    "users.dat":"1::F::1::10::00000\n", "ratings.dat":ratings
                }.items():
                    z.writestr("ml-1m/"+name, text.encode("latin-1"))
            with contextlib.redirect_stdout(io.StringIO()):
                result = convert(archive, root/"out")
            with (root/"out/movies.csv").open(encoding="utf-8") as f:
                movie_rows = list(csv.DictReader(f))
            return result,movie_rows

    def test_latin1_quoting_year_and_age_code(self):
        result, rows = self.run_fixture()
        self.assertEqual(rows[0]["title"],"Café, The (L'Associe)(1982)")
        self.assertEqual(rows[0]["year"],"1982")
        self.assertEqual(result["has_genre"],2)

    def test_duplicate_rating_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate rating"):
            self.run_fixture(ratings="1::1::5::100\n1::1::4::101\n")

    def test_orphan_rejected(self):
        with self.assertRaisesRegex(ValueError,"orphan"):
            self.run_fixture(ratings="1::2::5::100\n")

    def test_bad_rating_rejected(self):
        with self.assertRaisesRegex(ValueError,"invalid"):
            self.run_fixture(ratings="1::1::6::100\n")

    def test_missing_year_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing year"):
            self.run_fixture(movies="1::No year::Drama\n")


if __name__ == "__main__":
    unittest.main()

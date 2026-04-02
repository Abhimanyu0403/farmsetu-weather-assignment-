from django.test import SimpleTestCase

from climate.services.metoffice import build_url, parse

DATE_SAMPLE = """\
Areal values from HadUK-Grid 1km gridded climate data from land surface network
Source: Met Office National Climate Information Centre
Monthly, seasonal and annual mean air temperature for UK
Areal series, starting in 1884
Last updated 01-Apr-2026 11:34
year    jan    feb    mar    apr    may    jun    jul    aug    sep    oct    nov    dec     win     spr     sum     aut     ann
1884    5.0    4.2    5.1    6.2    9.7   12.5   14.5   15.3   13.0    8.3    4.6    3.3     ---    6.98   14.11    8.62    8.48
1885    2.0    4.2    3.5    6.6    7.6   12.3   14.5   12.4   10.9    6.2    4.8    3.0    3.14    5.92   13.09    7.28    7.36
"""

RANKED_SAMPLE = """\
Areal values from HadUK-Grid 1km gridded climate data from land surface network
Source: Met Office National Climate Information Centre
Monthly, seasonal and annual mean air temperature for UK
Areal series, starting in 1884
Last updated 01-Apr-2026 11:34
    jan  year    feb  year    ann  year
    6.3  1916    6.8  1998   10.09  2025
    5.9  2007    6.3  2024   10.03  2022
"""


class TestBuildUrl(SimpleTestCase):
    def test_url_format(self):
        url = build_url("Tmean", "date", "UK")
        assert url == (
            "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets"
            "/Tmean/date/UK.txt"
        )


class TestParseDateDataset(SimpleTestCase):
    def setUp(self):
        self.result = parse(DATE_SAMPLE)

    def test_order_type_detected(self):
        assert len(self.result["rows"]) == 2

    def test_metadata_title(self):
        assert self.result["metadata"]["title"] == (
            "Monthly, seasonal and annual mean air temperature for UK"
        )

    def test_metadata_series_start_year(self):
        assert self.result["metadata"]["series_start_year"] == 1884

    def test_metadata_last_updated(self):
        assert self.result["metadata"]["last_updated_text"] == "01-Apr-2026 11:34"

    def test_first_row_year(self):
        assert self.result["rows"][0]["year"] == 1884

    def test_first_row_jan(self):
        assert self.result["rows"][0]["jan"] == 5.0

    def test_missing_value_is_none(self):
        # 1884 win is "---"
        assert self.result["rows"][0]["win"] is None

    def test_second_row_win_present(self):
        assert self.result["rows"][1]["win"] == 3.14


class TestParseRankedDataset(SimpleTestCase):
    def setUp(self):
        self.result = parse(RANKED_SAMPLE)

    def test_row_count(self):
        # 2 ranks × 3 periods = 6 rows
        assert len(self.result["rows"]) == 6

    def test_first_row_structure(self):
        row = self.result["rows"][0]
        assert row == {"period_code": "jan", "rank": 1, "year": 1916, "value": 6.3}

    def test_period_codes_present(self):
        codes = {r["period_code"] for r in self.result["rows"]}
        assert codes == {"jan", "feb", "ann"}

    def test_rank_sequence(self):
        jan_rows = [r for r in self.result["rows"] if r["period_code"] == "jan"]
        assert [r["rank"] for r in jan_rows] == [1, 2]

    def test_metadata_series_start_year(self):
        assert self.result["metadata"]["series_start_year"] == 1884

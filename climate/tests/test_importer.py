from unittest.mock import patch

from django.test import TestCase

from climate.models import ClimateDataset, ClimateObservation, ClimateRankedStat
from climate.services.importer import import_dataset

PARSED_DATE = {
    "metadata": {
        "title": "Mean temperature for UK",
        "series_start_year": 1884,
        "last_updated_text": "01-Apr-2026 11:34",
    },
    "rows": [
        {"year": 1884, "jan": 5.0, "feb": 4.2, "mar": 5.1, "apr": 6.2,
         "may": 9.7, "jun": 12.5, "jul": 14.5, "aug": 15.3, "sep": 13.0,
         "oct": 8.3, "nov": 4.6, "dec": 3.3, "win": None, "spr": 6.98,
         "sum": 14.11, "aut": 8.62, "ann": 8.48},
        {"year": 1885, "jan": 2.0, "feb": 4.2, "mar": 3.5, "apr": 6.6,
         "may": 7.6, "jun": 12.3, "jul": 14.5, "aug": 12.4, "sep": 10.9,
         "oct": 6.2, "nov": 4.8, "dec": 3.0, "win": 3.14, "spr": 5.92,
         "sum": 13.09, "aut": 7.28, "ann": 7.36},
    ],
}

PARSED_RANKED = {
    "metadata": {
        "title": "Mean temperature for UK",
        "series_start_year": 1884,
        "last_updated_text": "01-Apr-2026 11:34",
    },
    "rows": [
        {"period_code": "jan", "rank": 1, "year": 1916, "value": 6.3},
        {"period_code": "jan", "rank": 2, "year": 2007, "value": 5.9},
        {"period_code": "ann", "rank": 1, "year": 2025, "value": 10.09},
    ],
}


def _mock_import(parsed_data, order_type):
    """Patch fetch_text to return a sentinel and parse to return parsed_data."""
    return (
        patch("climate.services.importer.fetch_text", return_value="raw"),
        patch("climate.services.importer.parse", return_value=parsed_data),
    )


class TestImportDateDataset(TestCase):
    def setUp(self):
        with patch("climate.services.importer.fetch_text", return_value="raw"), \
             patch("climate.services.importer.parse", return_value=PARSED_DATE):
            self.dataset = import_dataset(
                region_code="UK",
                region_name="United Kingdom",
                parameter_code="Tmean",
                parameter_name="Mean temperature",
                order_type="date",
            )

    def test_dataset_created(self):
        assert ClimateDataset.objects.count() == 1

    def test_dataset_metadata(self):
        ds = ClimateDataset.objects.get()
        assert ds.title == "Mean temperature for UK"
        assert ds.series_start_year == 1884
        assert ds.last_updated_text == "01-Apr-2026 11:34"
        assert ds.source_url == (
            "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets"
            "/Tmean/date/UK.txt"
        )

    def test_observations_created(self):
        assert self.dataset.observations.count() == 2

    def test_observation_values(self):
        obs = self.dataset.observations.get(year=1884)
        assert obs.jan == 5.0
        assert obs.win is None

    def test_reimport_replaces_observations(self):
        with patch("climate.services.importer.fetch_text", return_value="raw"), \
             patch("climate.services.importer.parse", return_value=PARSED_DATE):
            import_dataset("UK", "United Kingdom", "Tmean", "Mean temperature", "date")

        assert ClimateDataset.objects.count() == 1
        assert ClimateObservation.objects.count() == 2


class TestImportRankedDataset(TestCase):
    def setUp(self):
        with patch("climate.services.importer.fetch_text", return_value="raw"), \
             patch("climate.services.importer.parse", return_value=PARSED_RANKED):
            self.dataset = import_dataset(
                region_code="UK",
                region_name="United Kingdom",
                parameter_code="Tmean",
                parameter_name="Mean temperature",
                order_type="ranked",
            )

    def test_ranked_stats_created(self):
        assert self.dataset.ranked_stats.count() == 3

    def test_ranked_stat_values(self):
        stat = self.dataset.ranked_stats.get(period_code="jan", rank=1)
        assert stat.year == 1916
        assert stat.value == 6.3

    def test_reimport_replaces_ranked_stats(self):
        with patch("climate.services.importer.fetch_text", return_value="raw"), \
             patch("climate.services.importer.parse", return_value=PARSED_RANKED):
            import_dataset("UK", "United Kingdom", "Tmean", "Mean temperature", "ranked")

        assert ClimateDataset.objects.count() == 1
        assert ClimateRankedStat.objects.count() == 3

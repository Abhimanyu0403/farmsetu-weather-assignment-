from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from climate.models import ClimateDataset, ClimateObservation, ClimateRankedStat


def make_dataset(**kwargs) -> ClimateDataset:
    defaults = dict(
        region_code="UK",
        region_name="United Kingdom",
        parameter_code="Tmean",
        parameter_name="Mean temperature",
        order_type="date",
        source_url="https://example.com/data.txt",
        title="Mean temperature for UK",
        series_start_year=1884,
        last_updated_text="01-Apr-2026",
    )
    defaults.update(kwargs)
    return ClimateDataset.objects.create(**defaults)


class TestOptionsEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_returns_200(self):
        response = self.client.get("/api/options/")
        assert response.status_code == 200

    def test_response_keys(self):
        data = self.client.get("/api/options/").json()
        assert set(data.keys()) == {"regions", "parameters", "order_types"}

    def test_regions_not_empty(self):
        data = self.client.get("/api/options/").json()
        assert len(data["regions"]) > 0


class TestDatasetListEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_empty_list(self):
        response = self.client.get("/api/datasets/")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_stored_datasets(self):
        make_dataset()
        response = self.client.get("/api/datasets/")
        assert len(response.json()) == 1
        assert response.json()[0]["region_code"] == "UK"


class TestDatasetLoadEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "region_code": "UK",
            "region_name": "United Kingdom",
            "parameter_code": "Tmean",
            "parameter_name": "Mean temperature",
            "order_type": "date",
        }

    def test_missing_field_returns_400(self):
        response = self.client.post("/api/datasets/load/", {"region_code": "UK"}, format="json")
        assert response.status_code == 400
        assert "error" in response.json()

    def test_successful_load_returns_201(self):
        dataset = make_dataset()
        with patch("climate.api.import_dataset", return_value=dataset):
            response = self.client.post("/api/datasets/load/", self.payload, format="json")
        assert response.status_code == 201
        assert response.json()["region_code"] == "UK"

    def test_import_error_returns_502(self):
        with patch("climate.api.import_dataset", side_effect=Exception("network error")):
            response = self.client.post("/api/datasets/load/", self.payload, format="json")
        assert response.status_code == 502
        assert "network error" in response.json()["error"]


class TestObservationListEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.dataset = make_dataset()
        ClimateObservation.objects.create(dataset=self.dataset, year=1884, jan=5.0, ann=8.48)
        ClimateObservation.objects.create(dataset=self.dataset, year=1885, jan=2.0, ann=7.36)
        ClimateObservation.objects.create(dataset=self.dataset, year=1886, jan=1.1, ann=7.45)

    def test_missing_dataset_id_returns_400(self):
        response = self.client.get("/api/observations/")
        assert response.status_code == 400

    def test_returns_all_rows(self):
        response = self.client.get(f"/api/observations/?dataset_id={self.dataset.id}")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_from_year_filter(self):
        response = self.client.get(f"/api/observations/?dataset_id={self.dataset.id}&from_year=1885")
        assert len(response.json()) == 2

    def test_to_year_filter(self):
        response = self.client.get(f"/api/observations/?dataset_id={self.dataset.id}&to_year=1885")
        assert len(response.json()) == 2

    def test_year_range_filter(self):
        response = self.client.get(
            f"/api/observations/?dataset_id={self.dataset.id}&from_year=1885&to_year=1885"
        )
        assert len(response.json()) == 1
        assert response.json()[0]["year"] == 1885


class TestRankingListEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.dataset = make_dataset(order_type="ranked")
        ClimateRankedStat.objects.create(dataset=self.dataset, period_code="jan", rank=1, year=1916, value=6.3)
        ClimateRankedStat.objects.create(dataset=self.dataset, period_code="jan", rank=2, year=2007, value=5.9)
        ClimateRankedStat.objects.create(dataset=self.dataset, period_code="ann", rank=1, year=2025, value=10.09)

    def test_missing_params_returns_400(self):
        response = self.client.get("/api/rankings/")
        assert response.status_code == 400

    def test_missing_period_code_returns_400(self):
        response = self.client.get(f"/api/rankings/?dataset_id={self.dataset.id}")
        assert response.status_code == 400

    def test_returns_correct_period(self):
        response = self.client.get(f"/api/rankings/?dataset_id={self.dataset.id}&period_code=jan")
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(r["period_code"] == "jan" for r in response.json())

    def test_limit_param(self):
        response = self.client.get(
            f"/api/rankings/?dataset_id={self.dataset.id}&period_code=jan&limit=1"
        )
        assert len(response.json()) == 1
        assert response.json()[0]["rank"] == 1

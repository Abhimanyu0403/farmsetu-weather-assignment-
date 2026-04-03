from django.urls import path

from . import api, views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("health/", views.health, name="health"),
    path("api/options/", api.options, name="api-options"),
    path("api/datasets/", api.dataset_list, name="api-dataset-list"),
    path("api/datasets/load/", api.dataset_load, name="api-dataset-load"),
    path("api/observations/", api.observation_list, name="api-observation-list"),
    path("api/rankings/", api.ranking_list, name="api-ranking-list"),
]

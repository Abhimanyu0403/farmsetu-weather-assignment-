from django.contrib import admin

from .models import ClimateDataset, ClimateObservation, ClimateRankedStat


@admin.register(ClimateDataset)
class ClimateDatasetAdmin(admin.ModelAdmin):
    list_display = ("region_name", "parameter_name", "order_type", "series_start_year")
    list_filter = ("order_type", "region_name")
    search_fields = ("region_code", "parameter_code", "title")


@admin.register(ClimateObservation)
class ClimateObservationAdmin(admin.ModelAdmin):
    list_display = ("dataset", "year", "ann")
    list_filter = ("dataset",)
    ordering = ("dataset", "year")


@admin.register(ClimateRankedStat)
class ClimateRankedStatAdmin(admin.ModelAdmin):
    list_display = ("dataset", "period_code", "rank", "year", "value")
    list_filter = ("dataset", "period_code")

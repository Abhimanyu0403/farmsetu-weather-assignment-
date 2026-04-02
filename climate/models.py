from django.db import models


class ClimateDataset(models.Model):
    class OrderType(models.TextChoices):
        DATE = "date", "Date"
        RANKED = "ranked", "Ranked"

    region_code = models.CharField(max_length=20)
    region_name = models.CharField(max_length=100)
    parameter_code = models.CharField(max_length=20)
    parameter_name = models.CharField(max_length=100)
    order_type = models.CharField(max_length=10, choices=OrderType.choices)
    source_url = models.URLField()
    title = models.CharField(max_length=200)
    series_start_year = models.PositiveSmallIntegerField(null=True, blank=True)
    last_updated_text = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ("region_code", "parameter_code", "order_type")

    def __str__(self):
        return f"{self.region_name} — {self.parameter_name} ({self.order_type})"


class ClimateObservation(models.Model):
    dataset = models.ForeignKey(
        ClimateDataset, on_delete=models.CASCADE, related_name="observations"
    )
    year = models.PositiveSmallIntegerField()

    jan = models.FloatField(null=True, blank=True)
    feb = models.FloatField(null=True, blank=True)
    mar = models.FloatField(null=True, blank=True)
    apr = models.FloatField(null=True, blank=True)
    may = models.FloatField(null=True, blank=True)
    jun = models.FloatField(null=True, blank=True)
    jul = models.FloatField(null=True, blank=True)
    aug = models.FloatField(null=True, blank=True)
    sep = models.FloatField(null=True, blank=True)
    oct = models.FloatField(null=True, blank=True)
    nov = models.FloatField(null=True, blank=True)
    dec = models.FloatField(null=True, blank=True)
    win = models.FloatField(null=True, blank=True)
    spr = models.FloatField(null=True, blank=True)
    sum = models.FloatField(null=True, blank=True)
    aut = models.FloatField(null=True, blank=True)
    ann = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("dataset", "year")
        ordering = ["year"]

    def __str__(self):
        return f"{self.dataset} — {self.year}"


class ClimateRankedStat(models.Model):
    dataset = models.ForeignKey(
        ClimateDataset, on_delete=models.CASCADE, related_name="ranked_stats"
    )
    period_code = models.CharField(max_length=10)
    rank = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    value = models.FloatField()

    class Meta:
        unique_together = ("dataset", "period_code", "rank")
        indexes = [
            models.Index(fields=["dataset", "period_code"]),
        ]
        ordering = ["period_code", "rank"]

    def __str__(self):
        return f"{self.dataset} — {self.period_code} rank {self.rank} ({self.year})"

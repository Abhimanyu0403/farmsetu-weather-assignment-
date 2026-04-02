from rest_framework import serializers

from .models import ClimateDataset, ClimateObservation, ClimateRankedStat


class ClimateDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClimateDataset
        fields = "__all__"


class ClimateObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClimateObservation
        exclude = ("dataset",)


class ClimateRankedStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClimateRankedStat
        exclude = ("dataset",)

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .constants import ORDER_TYPES, PARAMETERS, REGIONS
from .models import ClimateDataset, ClimateObservation, ClimateRankedStat
from .serializers import (
    ClimateDatasetSerializer,
    ClimateObservationSerializer,
    ClimateRankedStatSerializer,
)
from .services.importer import import_dataset


@api_view(["GET"])
def options(request):
    return Response({
        "regions": REGIONS,
        "parameters": PARAMETERS,
        "order_types": ORDER_TYPES,
    })


@api_view(["GET"])
def dataset_list(request):
    datasets = ClimateDataset.objects.all()
    return Response(ClimateDatasetSerializer(datasets, many=True).data)


@api_view(["POST"])
def dataset_load(request):
    required = ("region_code", "region_name", "parameter_code", "parameter_name", "order_type")
    missing = [f for f in required if not request.data.get(f)]
    if missing:
        return Response({"error": f"Missing fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        dataset = import_dataset(
            region_code=request.data["region_code"],
            region_name=request.data["region_name"],
            parameter_code=request.data["parameter_code"],
            parameter_name=request.data["parameter_name"],
            order_type=request.data["order_type"],
        )
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    return Response(ClimateDatasetSerializer(dataset).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def observation_list(request):
    dataset_id = request.query_params.get("dataset_id")
    if not dataset_id:
        return Response({"error": "dataset_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    qs = ClimateObservation.objects.filter(dataset_id=dataset_id)

    from_year = request.query_params.get("from_year")
    to_year = request.query_params.get("to_year")
    if from_year:
        qs = qs.filter(year__gte=int(from_year))
    if to_year:
        qs = qs.filter(year__lte=int(to_year))

    return Response(ClimateObservationSerializer(qs, many=True).data)


@api_view(["GET"])
def ranking_list(request):
    dataset_id = request.query_params.get("dataset_id")
    period_code = request.query_params.get("period_code")

    if not dataset_id or not period_code:
        return Response(
            {"error": "dataset_id and period_code are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = ClimateRankedStat.objects.filter(dataset_id=dataset_id, period_code=period_code)

    limit = request.query_params.get("limit")
    if limit:
        qs = qs[:int(limit)]

    return Response(ClimateRankedStatSerializer(qs, many=True).data)

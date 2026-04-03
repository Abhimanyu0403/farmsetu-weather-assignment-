from django.db import transaction

from climate.models import ClimateDataset, ClimateObservation, ClimateRankedStat
from climate.services.metoffice import build_url, fetch_text, parse


@transaction.atomic
def import_dataset(
    region_code: str,
    region_name: str,
    parameter_code: str,
    parameter_name: str,
    order_type: str,
) -> ClimateDataset:
    url = build_url(parameter_code, order_type, region_code)
    parsed = parse(fetch_text(url))
    meta = parsed["metadata"]

    dataset, _ = ClimateDataset.objects.update_or_create(
        region_code=region_code,
        parameter_code=parameter_code,
        order_type=order_type,
        defaults={
            "region_name": region_name,
            "parameter_name": parameter_name,
            "source_url": url,
            "title": meta["title"],
            "series_start_year": meta["series_start_year"],
            "last_updated_text": meta["last_updated_text"],
        },
    )

    if order_type == ClimateDataset.OrderType.DATE:
        dataset.observations.all().delete()
        ClimateObservation.objects.bulk_create(
            [ClimateObservation(dataset=dataset, **row) for row in parsed["rows"]]
        )
    else:
        dataset.ranked_stats.all().delete()
        ClimateRankedStat.objects.bulk_create(
            [ClimateRankedStat(dataset=dataset, **row) for row in parsed["rows"]]
        )

    return dataset
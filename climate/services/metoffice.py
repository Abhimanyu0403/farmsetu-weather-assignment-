import re

import requests

BASE_URL = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets"

DATE_COLUMNS = ["year", "jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec",
                "win", "spr", "sum", "aut", "ann"]


def build_url(parameter: str, order: str, region: str) -> str:
    return f"{BASE_URL}/{parameter}/{order}/{region}.txt"


def fetch_text(url: str) -> str:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.text


def _parse_value(raw: str) -> float | None:
    stripped = raw.strip()
    if stripped == "---" or stripped == "":
        return None
    return float(stripped)


def _extract_metadata(lines: list[str]) -> dict:
    metadata = {"title": "", "series_start_year": None, "last_updated_text": ""}

    if lines:
        metadata["title"] = lines[2].strip() if len(lines) > 2 else lines[0].strip()

    for line in lines:
        match = re.search(r"starting in (\d{4})", line)
        if match:
            metadata["series_start_year"] = int(match.group(1))

        match = re.search(r"Last updated (.+)", line, re.IGNORECASE)
        if match:
            metadata["last_updated_text"] = match.group(1).strip()

    return metadata


def _is_date_header(line: str) -> bool:
    return line.strip().lower().startswith("year")


def _is_ranked_header(line: str) -> bool:
    stripped = line.strip().lower()
    return stripped.startswith("jan") and "year" in stripped


def _parse_date(lines: list[str], header_idx: int) -> list[dict]:
    rows = []
    for line in lines[header_idx + 1:]:
        parts = line.split()
        if not parts or not parts[0].isdigit():
            continue
        if len(parts) < 2:
            continue
        row = {"year": int(parts[0])}
        for i, col in enumerate(DATE_COLUMNS[1:], start=1):
            row[col] = _parse_value(parts[i]) if i < len(parts) else None
        rows.append(row)
    return rows


def _parse_ranked(lines: list[str], header_idx: int) -> list[dict]:
    header_parts = lines[header_idx].split()
    # header alternates: period_code  year  period_code  year ...
    period_codes = [header_parts[i] for i in range(0, len(header_parts), 2)]

    rows = []
    for rank_idx, line in enumerate(lines[header_idx + 1:], start=1):
        parts = line.split()
        if not parts:
            continue
        # each pair: value, year
        for col_idx, period_code in enumerate(period_codes):
            value_idx = col_idx * 2
            year_idx = value_idx + 1
            if year_idx >= len(parts):
                break
            value = _parse_value(parts[value_idx])
            year = _parse_value(parts[year_idx])
            if value is None or year is None:
                continue
            rows.append({
                "period_code": period_code,
                "rank": rank_idx,
                "year": int(year),
                "value": value,
            })
    return rows


def parse(text: str) -> dict:
    lines = text.splitlines()

    header_idx = None
    order_type = None
    for i, line in enumerate(lines):
        if _is_date_header(line):
            header_idx, order_type = i, "date"
            break
        if _is_ranked_header(line):
            header_idx, order_type = i, "ranked"
            break

    if header_idx is None:
        raise ValueError("Could not detect a recognised header line in the dataset.")

    metadata = _extract_metadata(lines[:header_idx])

    if order_type == "date":
        rows = _parse_date(lines, header_idx)
    else:
        rows = _parse_ranked(lines, header_idx)

    return {"metadata": metadata, "rows": rows}

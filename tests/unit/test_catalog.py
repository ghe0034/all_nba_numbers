import json

import pytest

from nba_ingest.catalog import load_endpoints, parse_endpoints


def valid_catalog(**overrides):
    entry = {
        "url": "https://stats.nba.com/stats/demo",
        "fixedParams": {"LeagueID": "00"},
        "seasonParamName": "Season",
    }
    entry.update(overrides)
    return {"demo": entry}


def test_parse_endpoints_builds_definition_from_entry():
    endpoint = parse_endpoints(valid_catalog())[0]

    assert endpoint.id == "demo"
    assert endpoint.url == "https://stats.nba.com/stats/demo"
    assert endpoint.season_param_name == "Season"
    assert endpoint.fixed_params == {"LeagueID": "00"}


def test_parse_endpoints_rejects_missing_required_field():
    catalog = valid_catalog()
    del catalog["demo"]["url"]

    with pytest.raises(ValueError, match="url"):
        parse_endpoints(catalog)


def test_parse_endpoints_rejects_season_inside_fixed_params():
    catalog = valid_catalog(fixedParams={"Season": "2025-26"})

    with pytest.raises(ValueError, match="Season"):
        parse_endpoints(catalog)


def test_load_endpoints_reads_catalog_file(tmp_path):
    catalog_file = tmp_path / "endpoints.json"
    catalog_file.write_text(json.dumps(valid_catalog()), encoding="utf-8")

    endpoints = load_endpoints(catalog_file)

    assert [endpoint.id for endpoint in endpoints] == ["demo"]

import json

import pytest

from nba_ingest.catalog import load_endpoints, parse_endpoints


def valid_entry(**overrides):
    entry = {
        "id": "endpoint_demo",
        "path": "/stats/demo",
        "season_param_name": "Season",
        "fixed_params": {"LeagueID": "00"},
    }
    entry.update(overrides)
    return entry


def test_parse_endpoints_builds_definition_from_entry():
    endpoint = parse_endpoints([valid_entry()])[0]

    assert endpoint.id == "endpoint_demo"
    assert endpoint.path == "/stats/demo"
    assert endpoint.season_param_name == "Season"
    assert endpoint.fixed_params == {"LeagueID": "00"}


def test_parse_endpoints_rejects_missing_required_field():
    entry = valid_entry()
    del entry["path"]

    with pytest.raises(ValueError, match="path"):
        parse_endpoints([entry])


def test_parse_endpoints_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="duplicad"):
        parse_endpoints([valid_entry(), valid_entry()])


def test_parse_endpoints_rejects_season_inside_fixed_params():
    entry = valid_entry(fixed_params={"Season": "2025-26"})

    with pytest.raises(ValueError, match="Season"):
        parse_endpoints([entry])


def test_load_endpoints_reads_catalog_file(tmp_path):
    catalog_file = tmp_path / "endpoints.json"
    catalog_file.write_text(json.dumps([valid_entry()]), encoding="utf-8")

    endpoints = load_endpoints(catalog_file)

    assert [endpoint.id for endpoint in endpoints] == ["endpoint_demo"]

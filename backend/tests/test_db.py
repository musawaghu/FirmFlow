"""Repo against the real supabase-py client, with PostgREST mocked at the HTTP layer."""

import json
from urllib.parse import unquote

import httpx
import pytest
from supabase import ClientOptions, create_client

from app.db import Repo


@pytest.fixture
def calls():
    return []


@pytest.fixture
def repo(calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=[{"id": "row-1"}])

    client = create_client(
        "https://proj.supabase.co",
        "service-role-key",
        ClientOptions(httpx_client=httpx.Client(transport=httpx.MockTransport(handler))),
    )
    return Repo(client)


def url(request):
    return unquote(str(request.url))


def test_select_filters_and_order(repo, calls):
    assert repo.select("manuals", {"firm_id": "f1", "status": ["uploaded", "failed"]}, order="created_at") == [{"id": "row-1"}]
    assert calls[0].method == "GET"
    assert url(calls[0]) == (
        "https://proj.supabase.co/rest/v1/manuals?select=*&firm_id=eq.f1&status=in.(uploaded,failed)&order=created_at.asc"
    )
    assert calls[0].headers["apikey"] == "service-role-key"


def test_select_with_empty_in_list_skips_the_request(repo, calls):
    assert repo.select("module_passages", {"module_id": []}) == []
    assert calls == []


def test_insert_sends_rows(repo, calls):
    repo.insert("issues", [{"id": "i1", "type": "broken_link"}])
    assert calls[0].method == "POST"
    assert json.loads(calls[0].content) == [{"id": "i1", "type": "broken_link"}]
    assert repo.insert("issues", []) == [] and len(calls) == 1


def test_update_targets_one_row(repo, calls):
    assert repo.update("manuals", "m1", {"status": "processing"}) == {"id": "row-1"}
    assert calls[0].method == "PATCH"
    assert url(calls[0]).endswith("/rest/v1/manuals?id=eq.m1")
    assert json.loads(calls[0].content) == {"status": "processing"}


def test_delete_requires_a_filter(repo, calls):
    repo.delete("modules", {"manual_id": "m1"})
    assert calls[0].method == "DELETE"
    assert url(calls[0]).endswith("/rest/v1/modules?manual_id=eq.m1")

    repo.delete("module_passages", {"module_id": []})  # nothing to delete
    assert len(calls) == 1
    with pytest.raises(ValueError):
        repo.delete("modules", {})

"""Supabase access for the backend.

The backend uses the service role key, so RLS doesn't apply: every query must
filter by the caller's firm itself. All table access goes through four small
Repo methods so routes and services stay easy to test with an in-memory fake.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

from supabase import Client, create_client

from app.config import get_settings

MANUALS_BUCKET = "manuals"

Row = dict[str, Any]
# Filter values: a scalar means "=", a list means "in".
Filters = dict[str, Any]


class NotConfigured(RuntimeError):
    """Supabase settings are missing; the API answers 503."""


class Repo:
    def __init__(self, client: Client):
        self.client = client

    def select(self, table: str, filters: Filters | None = None, order: str | None = None) -> list[Row]:
        query = self.client.table(table).select("*")
        for column, value in (filters or {}).items():
            if isinstance(value, list):
                if not value:
                    return []
                query = query.in_(column, value)
            else:
                query = query.eq(column, value)
        if order:
            query = query.order(order)
        return query.execute().data

    def select_one(self, table: str, filters: Filters) -> Row | None:
        rows = self.select(table, filters)
        return rows[0] if rows else None

    def insert(self, table: str, rows: list[Row]) -> list[Row]:
        if not rows:
            return []
        return self.client.table(table).insert(rows).execute().data

    def update(self, table: str, row_id: str, fields: Row) -> Row | None:
        data = self.client.table(table).update(fields).eq("id", row_id).execute().data
        return data[0] if data else None

    def delete(self, table: str, filters: Filters) -> None:
        if not filters:
            raise ValueError("Refusing to delete without a filter")
        query = self.client.table(table).delete()
        for column, value in filters.items():
            if isinstance(value, list):
                if not value:
                    return
                query = query.in_(column, value)
            else:
                query = query.eq(column, value)
        query.execute()


class Storage:
    def __init__(self, client: Client, bucket: str = MANUALS_BUCKET):
        self.bucket = client.storage.from_(bucket)

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        self.bucket.upload(path, data, {"content-type": content_type})

    def download(self, path: str) -> bytes:
        return self.bucket.download(path)

    def remove(self, path: str) -> None:
        self.bucket.remove([path])


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise NotConfigured("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    url = settings.supabase_url.strip().rstrip("/")
    if urlparse(url).path:
        raise NotConfigured(f"SUPABASE_URL should be just https://<ref>.supabase.co, without a path like /rest/v1 (got {url})")
    return create_client(url, settings.supabase_service_role_key.strip())


def get_repo() -> Repo:
    return Repo(get_supabase())


def get_storage() -> Storage:
    return Storage(get_supabase())

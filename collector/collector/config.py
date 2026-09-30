"""Collector configuration.

Non-secret settings live in a YAML file. Secrets (the author-hash salt and the
firm's backend API key) come from environment variables and are never written
to disk by the collector.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from collector.schema import MIN_SALT_LENGTH, Source

SALT_ENV = "COLLECTOR_AUTHOR_SALT"
API_KEY_ENV = "COLLECTOR_API_KEY"

# Hard floor for the smallest group a topic may describe. Below this, an
# "aggregate" can point at one or two identifiable people.
MIN_GROUP_SIZE_FLOOR = 3


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: Source
    channels: list[str] = Field(min_length=1)  # explicit allowlist, no wildcards

    @field_validator("channels")
    @classmethod
    def clean_channels(cls, v: list[str]) -> list[str]:
        cleaned = [c.strip() for c in v if c and c.strip()]
        if not cleaned:
            raise ValueError("channels must list at least one allowlisted channel")
        if any(c in ("*", "all") for c in cleaned):
            raise ValueError("wildcard channels are not allowed; list channels explicitly")
        return cleaned


class PrivacyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_group_size: int = Field(default=5, ge=MIN_GROUP_SIZE_FLOOR)
    raw_retention_days: int = Field(default=7, ge=0)
    initial_lookback_days: int = Field(default=30, ge=1)


class BackendConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str

    @field_validator("url")
    @classmethod
    def https_unless_local(cls, v: str) -> str:
        v = v.rstrip("/")
        local = v.startswith(("http://localhost", "http://127.0.0.1"))
        if not (v.startswith("https://") or local):
            raise ValueError("backend url must use https")
        return v


class CollectorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: BackendConfig
    privacy: PrivacyConfig = PrivacyConfig()
    sources: list[SourceConfig] = Field(min_length=1)
    state_path: str = "collector_state.db"

    # Filled from the environment, never from the YAML file.
    author_salt: str = Field(default="", exclude=True, repr=False)
    api_key: str = Field(default="", exclude=True, repr=False)

    @model_validator(mode="after")
    def unique_source_ids(self) -> "CollectorConfig":
        ids = [s.id for s in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("source ids must be unique")
        return self


class ConfigError(Exception):
    pass


def load_config(path: str | Path, env: Mapping[str, str] | None = None) -> CollectorConfig:
    env = os.environ if env is None else env
    try:
        raw = yaml.safe_load(Path(path).read_text()) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"could not read config: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("config must be a YAML mapping")
    forbidden = {"author_salt", "api_key"} & raw.keys()
    if forbidden:
        raise ConfigError(f"{sorted(forbidden)} must come from the environment, not the config file")

    salt = env.get(SALT_ENV, "")
    if len(salt) < MIN_SALT_LENGTH:
        raise ConfigError(f"set {SALT_ENV} to a secret of at least {MIN_SALT_LENGTH} characters")
    try:
        cfg = CollectorConfig.model_validate(raw)
    except Exception as exc:  # pydantic.ValidationError
        raise ConfigError(str(exc)) from exc
    cfg.author_salt = salt
    cfg.api_key = env.get(API_KEY_ENV, "")
    return cfg

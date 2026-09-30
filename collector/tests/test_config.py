import textwrap

import pytest

from collector.cli import main
from collector.config import API_KEY_ENV, SALT_ENV, ConfigError, load_config

GOOD = textwrap.dedent(
    """
    backend:
      url: https://firmflow.example
    sources:
      - id: slack-main
        type: slack
        channels: [C1, C2]
    """
)
ENV = {SALT_ENV: "a-long-enough-secret-salt", API_KEY_ENV: "key-123"}


def write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(text))
    return p


def test_valid_config_loads_with_defaults_and_env_secrets(tmp_path):
    cfg = load_config(write(tmp_path, GOOD), ENV)
    assert cfg.privacy.min_group_size == 5
    assert cfg.privacy.raw_retention_days == 7
    assert cfg.sources[0].channels == ["C1", "C2"]
    assert cfg.author_salt == ENV[SALT_ENV] and cfg.api_key == "key-123"


def test_secrets_never_appear_in_repr_or_dump(tmp_path):
    cfg = load_config(write(tmp_path, GOOD), ENV)
    assert ENV[SALT_ENV] not in repr(cfg) and "key-123" not in repr(cfg)
    assert "author_salt" not in cfg.model_dump() and "api_key" not in cfg.model_dump()


def test_salt_is_required(tmp_path):
    with pytest.raises(ConfigError, match=SALT_ENV):
        load_config(write(tmp_path, GOOD), {})
    with pytest.raises(ConfigError, match=SALT_ENV):
        load_config(write(tmp_path, GOOD), {SALT_ENV: "short"})


def test_secrets_in_the_file_are_refused(tmp_path):
    with pytest.raises(ConfigError, match="environment"):
        load_config(write(tmp_path, GOOD + "api_key: oops\n"), ENV)


def test_channels_must_be_explicit(tmp_path):
    empty = GOOD.replace("[C1, C2]", "[]")
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, empty), ENV)
    with pytest.raises(ConfigError, match="wildcard"):
        load_config(write(tmp_path, GOOD.replace("[C1, C2]", '["*"]')), ENV)


def test_group_size_has_a_floor(tmp_path):
    bad = GOOD + "privacy:\n  min_group_size: 2\n"
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, bad), ENV)
    ok = GOOD + "privacy:\n  min_group_size: 3\n"
    assert load_config(write(tmp_path, ok), ENV).privacy.min_group_size == 3


def test_backend_url_must_be_https_except_localhost(tmp_path):
    with pytest.raises(ConfigError, match="https"):
        load_config(write(tmp_path, GOOD.replace("https://firmflow.example", "http://firmflow.example")), ENV)
    local = GOOD.replace("https://firmflow.example", "http://localhost:8000")
    assert load_config(write(tmp_path, local), ENV).backend.url == "http://localhost:8000"


def test_duplicate_source_ids_unknown_types_and_unknown_keys_are_refused(tmp_path):
    dup = GOOD + "  - id: slack-main\n    type: teams\n    channels: [x]\n"
    with pytest.raises(ConfigError, match="unique"):
        load_config(write(tmp_path, dup), ENV)
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, GOOD.replace("type: slack", "type: irc")), ENV)
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, GOOD + "surprise: true\n"), ENV)


def test_missing_or_malformed_file(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "nope.yaml", ENV)
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, "- just\n- a list\n"), ENV)


def test_example_config_is_valid(monkeypatch):
    from pathlib import Path

    monkeypatch.setenv(SALT_ENV, ENV[SALT_ENV])
    cfg = load_config(Path(__file__).parent.parent / "config.example.yaml")
    assert {s.type.value for s in cfg.sources} == {"slack", "gmail"}


def test_cli_check_config(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(SALT_ENV, ENV[SALT_ENV])
    assert main(["check-config", str(write(tmp_path, GOOD))]) == 0
    out = capsys.readouterr().out
    assert "slack-main" in out and "C1, C2" in out
    monkeypatch.delenv(SALT_ENV)
    assert main(["check-config", str(write(tmp_path, GOOD))]) == 1

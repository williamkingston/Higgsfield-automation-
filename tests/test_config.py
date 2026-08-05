from __future__ import annotations

import pytest

from higgsfield.config import DEFAULT_API_BASE, HiggsfieldConfig
from higgsfield.errors import ConfigError


def test_from_env_reads_key_and_default_base(monkeypatch):
    monkeypatch.setenv("HIGGSFIELD_API_KEY", "secret-token")
    monkeypatch.delenv("HIGGSFIELD_API_BASE", raising=False)

    config = HiggsfieldConfig.from_env(load_dotenv_file=False)

    assert config.api_key == "secret-token"
    assert config.api_base == DEFAULT_API_BASE


def test_from_env_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("HIGGSFIELD_API_KEY", "secret-token")
    monkeypatch.setenv("HIGGSFIELD_API_BASE", "https://example.test/api/")

    config = HiggsfieldConfig.from_env(load_dotenv_file=False)

    assert config.api_base == "https://example.test/api"


def test_from_env_missing_key_raises(monkeypatch):
    monkeypatch.delenv("HIGGSFIELD_API_KEY", raising=False)

    with pytest.raises(ConfigError):
        HiggsfieldConfig.from_env(load_dotenv_file=False)


def test_repr_does_not_leak_key():
    config = HiggsfieldConfig(api_key="super-secret")
    assert "super-secret" not in repr(config)

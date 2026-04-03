import pytest


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token-123")
    monkeypatch.setenv("THINGS_API_HOST", "127.0.0.1")
    monkeypatch.setenv("THINGS_API_PORT", "9999")

    from things_api.config import Settings

    s = Settings()
    assert s.things_api_token.get_secret_value() == "test-token-123"
    assert s.things_api_host == "127.0.0.1"
    assert s.things_api_port == 9999


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    from things_api.config import Settings

    s = Settings()
    assert s.things_api_host == "0.0.0.0"
    assert s.things_api_port == 5225
    assert s.things_auth_token is None
    assert s.things_db_path is None
    assert s.things_verify_timeout == 0.5


def test_settings_requires_api_token(monkeypatch):
    monkeypatch.delenv("THINGS_API_TOKEN", raising=False)
    from things_api.config import Settings

    with pytest.raises(Exception):
        Settings()


def test_write_enabled_property(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "things-token")
    from things_api.config import Settings

    s = Settings()
    assert s.write_enabled is True


def test_write_disabled_without_auth_token(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.delenv("THINGS_AUTH_TOKEN", raising=False)
    from things_api.config import Settings

    s = Settings()
    assert s.write_enabled is False


def test_write_disabled_with_empty_auth_token(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "test-token")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "")
    from things_api.config import Settings

    s = Settings()
    assert s.write_enabled is False


def test_secret_str_repr_hides_tokens(monkeypatch):
    monkeypatch.setenv("THINGS_API_TOKEN", "super-secret")
    monkeypatch.setenv("THINGS_AUTH_TOKEN", "also-secret")
    from things_api.config import Settings

    s = Settings()
    settings_repr = repr(s)
    assert "super-secret" not in settings_repr
    assert "also-secret" not in settings_repr

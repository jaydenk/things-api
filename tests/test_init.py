import plistlib
from things_api.init import generate_token, detect_things_url_scheme, write_config


def test_generate_token():
    token = generate_token()
    assert token.startswith("tk_")
    assert len(token) > 20


def test_generate_token_unique():
    assert generate_token() != generate_token()


def test_detect_things_url_scheme_enabled(tmp_path):
    plist_dir = tmp_path / "Group Containers" / "JLMPQHK86H.com.culturedcode.ThingsMac" / "Library" / "Preferences"
    plist_dir.mkdir(parents=True)
    plist_file = plist_dir / "JLMPQHK86H.com.culturedcode.ThingsMac.plist"
    with open(plist_file, "wb") as f:
        plistlib.dump({"uriSchemeEnabled": True}, f)
    result = detect_things_url_scheme(search_root=tmp_path / "Group Containers")
    assert result is True


def test_detect_things_url_scheme_disabled(tmp_path):
    result = detect_things_url_scheme(search_root=tmp_path / "nonexistent")
    assert result is False


def test_write_config(tmp_path):
    config_file = tmp_path / "config"
    write_config(config_file, api_token="tk_test123", auth_token="things-auth-456", port=5225)
    content = config_file.read_text()
    assert "THINGS_API_TOKEN=tk_test123" in content
    assert "THINGS_AUTH_TOKEN=things-auth-456" in content
    assert "THINGS_API_PORT=5225" in content


def test_write_config_without_auth_token(tmp_path):
    config_file = tmp_path / "config"
    write_config(config_file, api_token="tk_test123", auth_token=None, port=5225)
    content = config_file.read_text()
    assert "THINGS_API_TOKEN=tk_test123" in content
    assert "THINGS_AUTH_TOKEN" not in content


def test_write_config_creates_parent_dirs(tmp_path):
    config_file = tmp_path / "deep" / "nested" / "config"
    write_config(config_file, api_token="tk_test", auth_token=None, port=5225)
    assert config_file.exists()

from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from things_api.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Things API" in result.output


def test_init_subcommand_creates_config(tmp_path):
    runner = CliRunner()
    config_file = tmp_path / "config"
    with patch("things_api.cli.CONFIG_FILE", config_file):
        with patch("things_api.cli.detect_things_url_scheme", return_value=False):
            result = runner.invoke(cli, ["init"], input="Y\n\n5225\n")
            assert result.exit_code == 0
            assert config_file.exists()
            content = config_file.read_text()
            assert "THINGS_API_TOKEN=tk_" in content


def test_init_detects_existing_config(tmp_path):
    runner = CliRunner()
    config_file = tmp_path / "config"
    config_file.write_text("THINGS_API_TOKEN=existing\n")
    with patch("things_api.cli.CONFIG_FILE", config_file):
        result = runner.invoke(cli, ["init"], input="n\n")
        assert result.exit_code == 0
        assert "already exists" in result.output.lower() or "overwrite" in result.output.lower()


def test_init_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--help"])
    assert result.exit_code == 0
    assert "setup wizard" in result.output.lower()

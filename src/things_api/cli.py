"""Click CLI for Things API."""

from __future__ import annotations

import logging
import sys

import click
import uvicorn

from things_api.config import CONFIG_FILE, Settings
from things_api.init import detect_things_url_scheme, generate_token, write_config


def _run_init() -> None:
    """Interactive setup wizard."""
    click.echo("Things API Setup")
    click.echo("=" * 40)
    click.echo()

    # 1. API Token
    click.echo("1. API Token")
    generate = click.confirm("   Generate a random token?", default=True)
    if generate:
        api_token = generate_token()
        click.echo(f"   Generated: {api_token}")
    else:
        api_token = click.prompt("   Enter your API token")
    click.echo()

    # 2. Things URL Scheme Auth Token
    click.echo("2. Things URL Scheme Auth Token")
    url_scheme_enabled = detect_things_url_scheme()
    if url_scheme_enabled:
        click.echo("   Things URL scheme is enabled.")
        click.echo("   To find your auth token, open Things > Settings > General > Enable Things URLs.")
        auth_token = click.prompt(
            "   Paste your Things auth token (or press Enter to skip)",
            default="",
            show_default=False,
        )
        if auth_token:
            click.echo("   Write operations enabled")
        else:
            auth_token = None
            click.echo("   Skipped — running in read-only mode")
    else:
        click.echo("   Things URL scheme is not enabled.")
        click.echo("   To enable writes, open Things > Settings > General > Enable Things URLs.")
        auth_token = None
        click.echo("   Skipped — running in read-only mode")
    click.echo()

    # 3. Port
    click.echo("3. Port")
    port = click.prompt("   Port", default=5225, type=int)
    click.echo()

    # Write config
    write_config(CONFIG_FILE, api_token, auth_token, port)
    click.echo(f"Config written to {CONFIG_FILE}")


@click.group(invoke_without_command=True)
@click.option("--token", default=None, help="API bearer token (overrides config file)")
@click.option("--port", default=None, type=int, help="Port to listen on (overrides config file)")
@click.pass_context
def cli(ctx: click.Context, token: str | None, port: int | None) -> None:
    """Things API — REST API for Things 3."""
    if ctx.invoked_subcommand is not None:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Try loading settings; if missing token, trigger init
    try:
        overrides = {}
        if token:
            overrides["things_api_token"] = token
        if port:
            overrides["things_api_port"] = port
        settings = Settings(**overrides)
    except Exception:
        if not CONFIG_FILE.exists() and sys.stdin.isatty():
            click.echo("No configuration found. Let's set one up.\n")
            _run_init()
            click.echo()
            settings = Settings()
        else:
            msg = (
                "Error: THINGS_API_TOKEN is not set.\n"
                "\n"
                "Run 'things-api init' to configure, or pass --token.\n"
            )
            if not sys.stdin.isatty():
                msg += f"Config file: {CONFIG_FILE}\n"
            click.echo(msg)
            raise SystemExit(1)

    from things_api.app import create_app

    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.things_api_host,
        port=settings.things_api_port,
    )


@cli.command()
def init() -> None:
    """Interactive setup wizard."""
    if CONFIG_FILE.exists():
        overwrite = click.confirm(
            f"Config already exists at {CONFIG_FILE}. Overwrite?",
            default=False,
        )
        if not overwrite:
            click.echo("Aborted.")
            return
    _run_init()

"""CLI to interact with the pipeline API suite.

The CLI expects the API server to be running. Start the server by running:

```
make run-container
```
"""

import json
from typing import Callable, TypeVar

import click
import httpx

from src.utils import get_basic_auth_header

BASE_URL = "http://0.0.0.0:5001"

F = TypeVar("F", bound=Callable)


def url_option(func: F) -> F:
    """Decorator to add the base URL option."""
    return click.option(
        "--base-url", default=BASE_URL, help="Base URL for the API server."
    )(func)


def auth_options(func: F) -> F:
    """Decorator to add authentication options."""
    func = click.option(
        "--username", required=True, help="Username for API authentication."
    )(func)
    func = click.option(
        "--password",
        required=True,
        hide_input=True,
        help="Password for API authentication.",
    )(func)
    return func


def get_headers(username: str, password: str) -> dict[str, str]:
    """Generate headers for API requests."""
    return {
        "Authorization": get_basic_auth_header(username, password),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


@click.group()
def cli() -> None:
    """Command-line interface for interacting with the pipeline API."""
    pass


@cli.command()
@auth_options
@url_option
@click.option(
    "--data", required=True, help="JSON data containing the pipeline configuration."
)
def create_pipeline(username: str, password: str, base_url: str, data: str) -> None:
    """Create a new pipeline from a JSON configuration."""
    headers = get_headers(username, password)
    url = f"{base_url}/v1/pipelines"
    try:
        json_data = json.loads(data)
    except json.JSONDecodeError:
        click.echo("Invalid JSON data.", err=True)
        return

    try:
        response = httpx.post(
            url, headers=headers, json=json_data, follow_redirects=True
        )
    except Exception as e:
        click.echo(
            f"An error occurred while creating the pipeline. Error: {e}", err=True
        )
        return

    click.echo(response.text)


@cli.command()
@auth_options
@url_option
@click.option("--pipeline-id", required=True, help="ID of the pipeline to retrieve.")
def get_pipeline(username: str, password: str, base_url: str, pipeline_id: str) -> None:
    """Retrieve a pipeline by its ID."""
    headers = get_headers(username, password)
    url = f"{base_url}/v1/pipelines/{pipeline_id}"

    try:
        response = httpx.get(url, headers=headers, follow_redirects=True)
    except Exception as e:
        click.echo(
            f"An error occurred while retrieving the pipeline. Error: {e}", err=True
        )
        return

    click.echo(response.text)


@cli.command()
@auth_options
@url_option
@click.option("--pipeline-id", required=True, help="ID of the pipeline to update.")
@click.option(
    "--data", required=True, help="JSON data containing the pipeline configuration."
)
def update_pipeline(
    username: str, password: str, base_url: str, pipeline_id: str, data: str
) -> None:
    """Update an existing pipeline configuration."""
    headers = get_headers(username, password)
    url = f"{base_url}/v1/pipelines/{pipeline_id}"

    try:
        json_data = json.loads(data)
    except json.JSONDecodeError:
        click.echo("Invalid JSON data.", err=True)
        return

    try:
        response = httpx.put(
            url, headers=headers, json=json_data, follow_redirects=True
        )
    except Exception as e:
        click.echo(
            f"An error occurred while updating the pipeline. Error: {e}", err=True
        )
        return

    click.echo(response.text)


@cli.command()
@auth_options
@url_option
@click.option("--pipeline-id", required=True, help="ID of the pipeline to trigger.")
def trigger_pipeline(
    username: str, password: str, base_url: str, pipeline_id: str
) -> None:
    """Trigger a pipeline by its ID."""
    headers = get_headers(username, password)
    url = f"{base_url}/v1/pipelines/{pipeline_id}/trigger"

    try:
        response = httpx.post(url, headers=headers, follow_redirects=True)
    except Exception as e:
        click.echo(
            f"An error occurred while triggering the pipeline. Error: {e}", err=True
        )
        return

    click.echo(response.text)


@cli.command()
@auth_options
@url_option
@click.option("--pipeline-id", required=True, help="ID of the pipeline to delete.")
def delete_pipeline(
    username: str, password: str, base_url: str, pipeline_id: str
) -> None:
    """Delete a pipeline by its ID."""
    headers = get_headers(username, password)
    url = f"{base_url}/v1/pipelines/{pipeline_id}"

    try:
        response = httpx.delete(url, headers=headers, follow_redirects=True)
    except Exception as e:
        click.echo(
            f"An error occurred while deleting the pipeline. Error: {e}", err=True
        )
        return

    click.echo(response.text)


if __name__ == "__main__":
    cli()

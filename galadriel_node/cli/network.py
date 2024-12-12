import asyncio
from http import HTTPStatus

import typer
from rich.table import Table

from galadriel_node.config import config
from galadriel_node.sdk.upgrade import version_aware_get
from galadriel_node.sdk.logging_utils import get_node_logger

network_app = typer.Typer(
    name="network",
    help="Galadriel tool to get network info",
    no_args_is_help=True,
)

logger = get_node_logger()


@network_app.command("stats", help="Get current network stats")
def network_stats(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
):
    config.validate()

    status, response_json = asyncio.run(
        version_aware_get(api_url, "network/stats", api_key)
    )

    if status == HTTPStatus.OK and response_json:
        print_network_status(response_json)
    else:
        # Using logger with rich formatting for error messages
        logger.error("[bold red]Failed to get node status..[/bold red]")


def print_network_status(data):
    # Using logger with rich formatting for info messages
    logger.info("[bold]nodes_count:[/bold] %s", data["nodes_count"])
    logger.info("[bold]connected_nodes_count:[/bold] %s", data["connected_nodes_count"])
    logger.info("[bold]network_throughput:[/bold] %s", data["network_throughput"])
    logger.info("[bold]throughput by model:[/bold]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Model Name", style="dim", width=20)
    table.add_column("Throughput", justify="right", style="dim", width=15)

    for model in data["network_models_stats"]:
        table.add_row(model["model_name"], str(model["throughput"]))

    # The RichHandler in the logger will handle the rendering of this table
    logger.info(table)

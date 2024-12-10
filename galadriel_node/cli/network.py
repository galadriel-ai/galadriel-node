import asyncio
from http import HTTPStatus

import typer

from rich.console import Console
from rich.table import Table
from rich import print as rprint

from galadriel_node.config import config
from galadriel_node.sdk.upgrade import version_aware_get

network_app = typer.Typer(
    name="network",
    help="Galadriel tool to get network info",
    no_args_is_help=True,
)

console = Console()

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
        rprint("[bold red]Failed to get node status..[/bold red]")

def print_network_status(data):
    console.print(f"[bold]nodes_count:[/bold] {data['nodes_count']}")
    console.print(f"[bold]connected_nodes_count:[/bold] {data['connected_nodes_count']}")
    console.print(f"[bold]network_throughput:[/bold] {data['network_throughput']}")

    console.print("[bold]throughput by model:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Model Name", style="dim", width=20)
    table.add_column("Throughput", justify="right", style="dim", width=15)

    for model in data["network_models_stats"]:
        table.add_row(model["model_name"], str(model["throughput"]))

    console.print(table)

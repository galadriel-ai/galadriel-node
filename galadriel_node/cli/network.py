import asyncio
from http import HTTPStatus

import typer

from galadriel_node.config import config
from galadriel_node.sdk.upgrade import version_aware_get

network_app = typer.Typer(
    name="network",
    help="Galadriel tool to get network info",
    no_args_is_help=True,
)


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
        print("Failed to get node status..", flush=True)


def print_network_status(data):
    print(f"nodes_count: {data['nodes_count']}")
    print(f"connected_nodes_count: {data['connected_nodes_count']}")
    print(f"network_throughput: {data['network_throughput']}")
    print("throughput by model:")

    for model in data["network_models_stats"]:
        print(f"    model_name: {model['model_name']}")
        print(f"    throughput: {model['throughput']}")
        print()

import asyncio
from http import HTTPStatus

import typer

from galadriel_node.config import config
from galadriel_node.sdk import api

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
    config.raise_if_no_dotenv()

    status, response_json = asyncio.run(api.get(api_url, "network/stats", api_key))
    if status == HTTPStatus.OK and response_json:
        print_network_status(response_json)
    elif status == HTTPStatus.UPGRADE_REQUIRED:
        print(
            "Error: Your CLI version is outdated. Please update to the latest version. You can find it at https://pypi.org/project/galadriel-node/"
        )
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

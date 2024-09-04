import asyncio

import typer

from galadriel_node.config import config
from galadriel_node.sdk import api

network_app = typer.Typer(
    name="network",
    help="Galadriel tool to get network info",
    no_args_is_help=True,
)


@network_app.command("stats", help="Get current network stats")
def node_status(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
):
    status, response_json = asyncio.run(api.get(api_url, "network/stats", api_key))
    if status == 200 and response_json:
        for k, v in response_json.items():
            print(f"{k}: {v}", flush=True)
    else:
        print("Failed to get node status..", flush=True)

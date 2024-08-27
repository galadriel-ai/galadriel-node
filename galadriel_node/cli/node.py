import asyncio
import json
import traceback
from typing import List

import typer
import websockets
from rich import print

from galadriel_node.config import config
from galadriel_node.sdk.llm import Llm
from galadriel_node.sdk.entities import InferenceRequest, InferenceResponse

llm = Llm()

node_app = typer.Typer(
    name="node",
    help="Galadriel tool to manage node",
    no_args_is_help=True,
)


@node_app.command("run", help="Run the Galadriel node")
def node_run(
    rpc_url: str = typer.Option(config.GALADRIEL_RPC_URL, help="RPC url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
    llm_base_url: str = typer.Option(
        config.GALADRIEL_LLM_BASE_URL, help="LLM base url"
    ),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    async def run_node():
        uri = f"{rpc_url}/ws"
        headers = {"Authorization": f"Bearer {api_key}"}
        async with websockets.connect(uri, extra_headers=headers) as websocket:
            print(f"Connected to {uri}")
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    request = InferenceRequest.from_dict(data)
                    async for chunk in llm.execute(request, llm_base_url):
                        if debug:
                            print(f"Sending chunk: {chunk}")
                        await websocket.send(chunk.to_json())
                except Exception as e:
                    if debug:
                        traceback.print_exc()

    asyncio.run(run_node())

import asyncio
import traceback
from typing import Optional

import typer
import websockets
from rich import print

from galadriel_node.config import config
from galadriel_node.sdk import api
from galadriel_node.sdk.entities import InferenceRequest
from galadriel_node.sdk.entities import SdkError
from galadriel_node.sdk.llm import Llm
from galadriel_node.sdk.system.report_hardware import report_hardware
from galadriel_node.sdk.system.report_performance import report_performance

llm = Llm()

node_app = typer.Typer(
    name="node",
    help="Galadriel tool to manage node",
    no_args_is_help=True,
)

MAX_RETRIES = 5
BACKOFF_MIN = 1  # Minimum backoff time in seconds


async def process_request(
    request: InferenceRequest,
    websocket,
    llm_base_url: str,
    debug: bool,
    send_lock: asyncio.Lock,
) -> None:
    """
    Handles a single inference request and sends the response back in chunks.
    """
    try:
        if debug:
            print(f"REQUEST {request.id} START", flush=True)
        async for chunk in llm.execute(request, llm_base_url):
            if debug:
                print(f"Sending chunk: {chunk}", flush=True)
            async with send_lock:
                await websocket.send(chunk.to_json())
        if debug:
            print(f"REQUEST {request.id} END", flush=True)
    except Exception as e:
        if debug:
            traceback.print_exc()
        print(f"Error occurred while processing inference request: {e}", flush=True)


async def connect_and_process(
    uri: str, headers: dict, llm_base_url: str, debug: bool
) -> bool:
    """
    Establishes the WebSocket connection and processes incoming requests concurrently.
    """
    send_lock = asyncio.Lock()

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        print(f"Connected to {uri}", flush=True)
        while True:
            try:
                message = await websocket.recv()
                request = InferenceRequest.from_json(message)

                asyncio.create_task(
                    process_request(request, websocket, llm_base_url, debug, send_lock)
                )
            except websockets.ConnectionClosed as e:
                if e.code == 1008:
                    print(
                        f"Received error: {e.reason}. Exiting...",
                        flush=True,
                    )
                    return False
                print(f"Connection closed: {e}. Exiting loop.", flush=True)
                return True
            except Exception as e:
                if debug:
                    traceback.print_exc()
                print(f"Error occurred while processing message: {e}", flush=True)
                return True


async def retry_connection(rpc_url: str, api_key: str, llm_base_url: str, debug: bool):
    """
    Attempts to reconnect to the Galadriel server with exponential backoff.
    """
    uri = f"{rpc_url}/ws"
    headers = {"Authorization": f"Bearer {api_key}", "Model": config.GALADRIEL_MODEL_ID}
    retries = 0
    backoff_time = BACKOFF_MIN

    while retries < MAX_RETRIES:
        try:
            retry = await connect_and_process(uri, headers, llm_base_url, debug)
            if not retry:
                break
            retries = 0  # Reset retries on successful connection
            backoff_time = BACKOFF_MIN  # Reset backoff time
        except websockets.ConnectionClosedError as e:
            retries += 1
            print(f"WebSocket connection closed: {e}. Retrying...", flush=True)
        except websockets.InvalidStatusCode as e:
            print("Invalid status code:", e, flush=True)
            break
        except Exception as e:
            retries += 1
            if debug:
                traceback.print_exc()
            print(
                f"Websocket connection failed ({retries}/{MAX_RETRIES}). Retrying in {backoff_time} seconds...",
                flush=True,
            )

        # Exponential backoff before retrying
        await asyncio.sleep(backoff_time)
        backoff_time = min(backoff_time * 2, 60)  # Cap backoff time to 60 seconds

        if retries >= MAX_RETRIES:
            print(
                "Max retries reached. Make sure GALADRIEL_RPC_URL is set correctly. Exiting...",
                flush=True,
            )
            break


async def run_node(
    api_url: str, rpc_url: str, api_key: Optional[str], llm_base_url: str, debug: bool
):
    if not api_key:
        raise Exception("GALADRIEL_API_KEY env variable not set")
    await report_hardware(api_url, api_key)
    await report_performance(api_url, api_key, llm_base_url, config.GALADRIEL_MODEL_ID)
    await retry_connection(rpc_url, api_key, llm_base_url, debug)


@node_app.command("run", help="Run the Galadriel node")
def node_run(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    rpc_url: str = typer.Option(config.GALADRIEL_RPC_URL, help="RPC url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
    llm_base_url: str = typer.Option(
        config.GALADRIEL_LLM_BASE_URL, help="LLM base url"
    ),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    """
    Entry point for running the node with retry logic and connection handling.
    """
    config.raise_if_no_dotenv()
    try:
        asyncio.run(run_node(api_url, rpc_url, api_key, llm_base_url, debug))
    except SdkError as e:
        print(f"Got an Exception when trying to run the node: \n{e}", flush=True)
    except Exception:
        print(f"Got an unexpected Exception when trying to run the node: ", flush=True)
        traceback.print_exc()


@node_app.command("status", help="Get node status")
def node_status(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
):
    config.raise_if_no_dotenv()
    status, response_json = asyncio.run(api.get(api_url, "node/info", api_key))
    if status == 200 and response_json:
        run_status = response_json.get("status")
        if run_status:
            if run_status == "online":
                status_text = typer.style(run_status, fg=typer.colors.GREEN, bold=True)
                typer.echo("status: " + status_text)
            else:
                status_text = typer.style(run_status, fg=typer.colors.RED, bold=True)
                typer.echo("status: " + status_text)
        run_duration = response_json.get("run_duration_seconds")
        if run_duration:
            print(f"run_duration_seconds: {run_duration}", flush=True)
        excluded_keys = ["status", "run_duration_seconds"]
        for k, v in response_json.items():
            if k not in excluded_keys:
                print(f"{k}: {v}", flush=True)
    elif status == 404:
        print("Node has not been registered yet..", flush=True)
    else:
        print("Failed to get node status..", flush=True)


@node_app.command("stats", help="Get node stats")
def node_status(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
):
    config.raise_if_no_dotenv()
    status, response_json = asyncio.run(api.get(api_url, "node/stats", api_key))
    if status == 200 and response_json:
        excluded_keys = ["completed_inferences"]
        for k, v in response_json.items():
            if k not in excluded_keys:
                print(f"{k}: {v if v is not None else '<UNKNOWN>'}", flush=True)
        if response_json.get("completed_inferences"):
            print("Latest completed inferences:", flush=True)
        for i in response_json.get("completed_inferences", []):
            print(i, flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(
            run_node(
                config.GALADRIEL_API_URL,
                config.GALADRIEL_RPC_URL,
                config.GALADRIEL_API_KEY,
                config.GALADRIEL_LLM_BASE_URL,
                True,
            )
        )
    except SdkError as e:
        print(f"Got an Exception when trying to run the node: \n{e}", flush=True)
    except Exception as e:
        print(f"Got an unexpected Exception when trying to run the node: ", flush=True)
        traceback.print_exc()

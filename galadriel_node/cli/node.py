import asyncio
import signal
import subprocess
import sys
import traceback
from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional
from urllib.parse import urljoin

import aiohttp
import openai
import rich
import typer
import websockets
from websockets.frames import CloseCode

from galadriel_node.config import config
from galadriel_node.llm_backends import vllm
from galadriel_node.sdk.entities import AuthenticationError, InferenceRequest, SdkError
from galadriel_node.sdk.llm import Llm
from galadriel_node.sdk.system.report_hardware import report_hardware
from galadriel_node.sdk.system.report_performance import report_performance
from galadriel_node.sdk.upgrade import version_aware_get

llm = Llm()

node_app = typer.Typer(
    name="node",
    help="Galadriel tool to manage node",
    no_args_is_help=True,
)

BACKOFF_MIN = 4  # Minimum backoff time in seconds
BACKOFF_MAX = 300  # Maximum backoff time in seconds


@dataclass
class ConnectionResult:
    retry: bool
    reset_backoff: bool = True


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
            rich.print(f"REQUEST {request.id} START", flush=True)
        async for chunk in llm.execute(request, llm_base_url):
            if debug:
                rich.print(f"Sending chunk: {chunk}", flush=True)
            async with send_lock:
                await websocket.send(chunk.to_json())
        if debug:
            rich.print(f"REQUEST {request.id} END", flush=True)
    except Exception as e:
        if debug:
            traceback.print_exc()
        rich.print(
            f"Error occurred while processing inference request: {e}", flush=True
        )


async def connect_and_process(
    uri: str, headers: dict, llm_base_url: str, debug: bool
) -> ConnectionResult:
    """
    Establishes the WebSocket connection and processes incoming requests concurrently.
    """
    send_lock = asyncio.Lock()

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        rich.print(f"Connected to {uri}", flush=True)
        while True:
            try:
                message = await websocket.recv()
                request = InferenceRequest.from_json(message)

                asyncio.create_task(
                    process_request(request, websocket, llm_base_url, debug, send_lock)
                )
            except websockets.ConnectionClosed as e:
                rich.print(
                    f"Received error: {e.reason}.",
                    flush=True,
                )
                match e.code:
                    case CloseCode.POLICY_VIOLATION:
                        return ConnectionResult(retry=False)
                    case CloseCode.TRY_AGAIN_LATER:
                        return ConnectionResult(retry=True, reset_backoff=False)
                rich.print(f"Connection closed: {e}.", flush=True)
                return ConnectionResult(retry=True, reset_backoff=True)
            except Exception as e:
                if debug:
                    traceback.print_exc()
                rich.print(f"Error occurred while processing message: {e}", flush=True)
                return ConnectionResult(retry=True, reset_backoff=True)


async def retry_connection(
    rpc_url: str, api_key: str, node_id: str, llm_base_url: str, debug: bool
):
    """
    Attempts to reconnect to the Galadriel server with exponential backoff.
    """
    uri = f"{rpc_url}/ws"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Model": config.GALADRIEL_MODEL_ID,
        "Node-Id": node_id,
    }
    retries = 0
    backoff_time = BACKOFF_MIN

    while True:
        try:
            result = await connect_and_process(uri, headers, llm_base_url, debug)
            if result.retry:
                retries += 1
                if result.reset_backoff:
                    retries = 0
                    backoff_time = BACKOFF_MIN
                rich.print(f"Retry #{retries} in {backoff_time} seconds...")
            else:
                break
        except websockets.ConnectionClosedError as e:
            retries += 1
            rich.print(f"WebSocket connection closed: {e}. Retrying...", flush=True)
        except websockets.InvalidStatusCode as e:
            retries += 1
            rich.print(f"Invalid status code: {e}. Retrying...", flush=True)
        except Exception as e:
            retries += 1
            if debug:
                traceback.print_exc()
            rich.print(
                f"Websocket connection failed. Retry #{retries} in {backoff_time} seconds...",
                flush=True,
            )

        # Exponential backoff before retrying
        await asyncio.sleep(backoff_time)
        backoff_time = min(backoff_time * 2, BACKOFF_MAX)


def handle_termination(loop, llm_pid):
    for task in asyncio.all_tasks(loop):
        task.cancel()

    if llm_pid is not None:
        vllm.stop(llm_pid)
        print(f"vLLM process with PID {llm_pid} has been stopped.")


async def run_node(
    api_url: str,
    rpc_url: str,
    api_key: Optional[str],
    node_id: Optional[str],
    llm_base_url: Optional[str],
    debug: bool,
):
    if not api_key:
        raise SdkError("GALADRIEL_API_KEY env variable not set")
    if not node_id:
        raise SdkError("GALADRIEL_NODE_ID env variable not set")

    # Check version compatibility with the backend. This way it doesn't have to be checked inside report* commands
    await version_aware_get(
        api_url, "node/info", api_key, query_params={"node_id": node_id}
    )
    try:
        if llm_base_url:
            result = await check_llm(llm_base_url, config.GALADRIEL_MODEL_ID)
            if not result:
                raise SdkError(
                    'LLM check failed. Please make sure "GALADRIEL_LLM_BASE_URL" is correct.'
                )
        else:
            llm_pid = await run_llm(config.GALADRIEL_MODEL_ID, debug)
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda: handle_termination(loop, llm_pid))
            llm_base_url = vllm.LLM_BASE_URL
        await report_hardware(api_url, api_key, node_id)
        await report_performance(
            api_url, api_key, node_id, llm_base_url, config.GALADRIEL_MODEL_ID
        )
        await retry_connection(rpc_url, api_key, node_id, llm_base_url, debug)
    except asyncio.CancelledError:
        rich.print("Stopping the node.", flush=True)


async def llm_http_check(llm_base_url: str, total_timeout: float = 60.0):
    timeout = aiohttp.ClientTimeout(total=total_timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        return await session.get(llm_base_url + "/v1/models/")


async def llm_sanity_check(
    llm_base_url: str,
    model_id: str,
):
    base_url: str = urljoin(llm_base_url, "/v1")
    client = openai.AsyncOpenAI(base_url=base_url, api_key="sk-no-key-required")
    return await client.chat.with_raw_response.completions.create(
        model=model_id,
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            },
        ],
        max_tokens=5,
        timeout=5,
    )


async def check_llm(llm_base_url: str, model_id: str) -> bool:
    try:
        response = await llm_http_check(llm_base_url)
        if response.ok:
            rich.print(
                f"[bold green]\N{CHECK MARK} LLM server at {llm_base_url} is accessible via HTTP."
                "[/bold green]",
                flush=True,
            )
        else:
            rich.print(
                f"[bold red]\N{CROSS MARK} LLM server at {llm_base_url} returned status code: "
                f"{response.status_code}[/bold red]",
                flush=True,
            )
            return False
    except Exception as e:
        rich.print(
            f"[bold red]\N{CROSS MARK} Failed to reach LLM server at {llm_base_url}: \n{e}[/bold red]",
            flush=True,
        )
        return False

    try:
        response = await llm_sanity_check(llm_base_url, model_id)
        if response.status_code == HTTPStatus.OK:
            rich.print(
                f"[bold green]\N{CHECK MARK} LLM server at {llm_base_url} successfully generated "
                "tokens.[/bold green]",
                flush=True,
            )
            return True
    except openai.APIStatusError as e:
        rich.print(
            f"[bold red]\N{CROSS MARK} LLM server at {llm_base_url} failed to generate tokens. "
            f"APIStatusError: \n{e}[/bold red]",
            flush=True,
        )
        return False
    except Exception as e:
        rich.print(
            f"[bold red]\N{CROSS MARK} LLM server at {llm_base_url} failed to generate tokens."
            f" Exception occurred: {e}[/bold red]",
            flush=True,
        )
        return False
    return False


async def run_llm(model_id: str, debug: bool = False) -> Optional[int]:
    if vllm.is_installed():
        rich.print("Starting vLLM...", flush=True)
        pid = vllm.start(model_id, debug)
        if pid is None:
            raise SdkError(
                'Failed to start vLLM. Please check "vllm.log" for more information.'
            )
        rich.print("vLLM started successfully.", flush=True)
        rich.print("Waiting for vLLM to be ready.", flush=True)
        while True:
            if not vllm.is_process_running(pid):
                raise SdkError(
                    f"vLLM process (PID: {pid}) died unexpectedly. Please check 'vllm.log'."
                )
            rich.print(".", flush=True, end="")
            try:
                response = await llm_http_check(vllm.LLM_BASE_URL, total_timeout=1.0)
                if response.ok:
                    rich.print("\nvLLM is ready.", flush=True)
                    break
            except Exception:
                continue
            finally:
                await asyncio.sleep(1.0)
        result = await check_llm(vllm.LLM_BASE_URL, model_id)
        if not result:
            raise SdkError(
                'LLM check failed. Please check "vllm.log" for more details.'
            )
        return pid
    raise SdkError(
        "vLLM is not installed, please set GALADRIEL_LLM_BASE_URL in ~/.galadrielenv"
    )


@node_app.command("run", help="Run the Galadriel node")
def node_run(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    rpc_url: str = typer.Option(config.GALADRIEL_RPC_URL, help="RPC url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
    node_id: str = typer.Option(config.GALADRIEL_NODE_ID, help="Node ID"),
    llm_base_url: Optional[str] = typer.Option(
        config.GALADRIEL_LLM_BASE_URL, help="LLM base url"
    ),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    """
    Entry point for running the node with retry logic and connection handling.
    """
    config.validate()
    try:
        asyncio.run(run_node(api_url, rpc_url, api_key, node_id, llm_base_url, debug))
    except AuthenticationError:
        rich.print(
            "Authentication failed. Please check your API key and try again.",
            flush=True,
        )
    except SdkError as e:
        rich.print(f"Got an Exception when trying to run the node: \n{e}", flush=True)
    except Exception:
        rich.print(
            "Got an unexpected Exception when trying to run the node: ", flush=True
        )
        traceback.print_exc()


@node_app.command("status", help="Get node status")
def node_status(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
    node_id: str = typer.Option(config.GALADRIEL_NODE_ID, help="Node ID"),
):
    config.validate()
    status, response_json = asyncio.run(
        version_aware_get(
            api_url, "node/info", api_key, query_params={"node_id": node_id}
        )
    )
    if status == HTTPStatus.OK and response_json:
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
            rich.print(f"run_duration_seconds: {run_duration}", flush=True)
        excluded_keys = ["status", "run_duration_seconds"]
        for k, v in response_json.items():
            if k not in excluded_keys:
                rich.print(f"{k}: {v}", flush=True)
    elif status == HTTPStatus.NOT_FOUND:
        rich.print("Node has not been registered yet..", flush=True)
    else:
        rich.print("Failed to get node status..", flush=True)


@node_app.command("llm-status", help="Get LLM status")
def llm_status(
    model_id: str = typer.Option(config.GALADRIEL_MODEL_ID, help="Model ID"),
    llm_base_url: Optional[str] = typer.Option(
        config.GALADRIEL_LLM_BASE_URL, help="LLM base url"
    ),
):
    config.validate()
    if not llm_base_url:
        llm_base_url = vllm.LLM_BASE_URL
    asyncio.run(check_llm(llm_base_url, model_id))


@node_app.command("stats", help="Get node stats")
def node_stats(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
    node_id: str = typer.Option(config.GALADRIEL_NODE_ID, help="Node ID"),
):
    config.validate()
    status, response_json = asyncio.run(
        version_aware_get(
            api_url, "node/stats", api_key, query_params={"node_id": node_id}
        )
    )
    if status == HTTPStatus.OK and response_json:
        excluded_keys = ["completed_inferences"]
        for k, v in response_json.items():
            if k not in excluded_keys:
                rich.print(f"{k}: {v if v is not None else '<UNKNOWN>'}", flush=True)
        if response_json.get("completed_inferences"):
            rich.print("Latest completed inferences:", flush=True)
        for i in response_json.get("completed_inferences", []):
            rich.print(i, flush=True)


@node_app.command("upgrade", help="Upgrade the node to the latest version")
def node_upgrade():
    try:
        print("Updating galadriel CLI to the latest version...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "galadriel"]
        )
        print("galadriel CLI has been successfully updated to the latest version.")
    except subprocess.CalledProcessError:
        print(
            "An error occurred while updating galadriel CLI. Please check your internet connection and try again."
        )
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(
            run_node(
                config.GALADRIEL_API_URL,
                config.GALADRIEL_RPC_URL,
                config.GALADRIEL_API_KEY,
                config.GALADRIEL_NODE_ID,
                config.GALADRIEL_LLM_BASE_URL,
                True,
            )
        )
    except SdkError as e:
        rich.print(f"Got an Exception when trying to run the node: \n{e}", flush=True)
    except Exception as e:
        rich.print(
            "Got an unexpected Exception when trying to run the node: ", flush=True
        )
        traceback.print_exc()

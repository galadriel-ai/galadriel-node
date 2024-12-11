import asyncio
import subprocess
import sys
from http import HTTPStatus
from typing import Optional

import rich
import typer

from galadriel_node.config import config
from galadriel_node.llm_backends import vllm
from galadriel_node.sdk import long_benchmark
from galadriel_node.sdk.entities import AuthenticationError
from galadriel_node.sdk.entities import SdkError
from galadriel_node.sdk.logging_utils import get_node_logger
from galadriel_node.sdk.logging_utils import init_logging
from galadriel_node.sdk.node import check_llm
from galadriel_node.sdk.node import run_node
from galadriel_node.sdk.upgrade import version_aware_get

node_app = typer.Typer(
    name="node",
    help="Galadriel tool to manage node",
    no_args_is_help=True,
)

logger = get_node_logger()


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
    init_logging(debug)
    config.validate()
    try:
        asyncio.run(run_node.execute(api_url, rpc_url, api_key, node_id, llm_base_url))
    except AuthenticationError:
        logger.error("Authentication failed. Please check your API key and try again.")
    except SdkError as e:
        logger.error(f"Got an Exception when trying to run the node: {e}")
    except Exception:
        logger.error(
            "Got an unexpected Exception when trying to run the node: ", exc_info=True
        )


@node_app.command("status", help="Get node status")
def node_status(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
    node_id: str = typer.Option(config.GALADRIEL_NODE_ID, help="Node ID"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    init_logging(debug)
    config.validate()
    status, response_json = asyncio.run(
        version_aware_get(
            api_url, "node/info", api_key, query_params={"node_id": node_id}
        )
    )
    if status == HTTPStatus.OK and response_json:
        run_status = response_json.get("status")
        if run_status:
            status_text = typer.style(run_status, fg=typer.colors.WHITE, bold=True)
            typer.echo("status: " + status_text)
        run_duration = response_json.get("run_duration_seconds")
        if run_duration:
            logger.info(f"run_duration_seconds: {run_duration}")
        excluded_keys = ["status", "run_duration_seconds"]
        for k, v in response_json.items():
            if k not in excluded_keys:
                rich.print(f"{k}: {v}", flush=True)
    elif status == HTTPStatus.NOT_FOUND:
        logger.info("Node has not been registered yet..")
    else:
        logger.info("Failed to get node status..")


@node_app.command("llm-status", help="Get LLM status")
def llm_status(
    model_id: str = typer.Option(config.GALADRIEL_MODEL_ID, help="Model ID"),
    llm_base_url: Optional[str] = typer.Option(
        config.GALADRIEL_LLM_BASE_URL, help="LLM base url"
    ),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    init_logging(debug)
    config.validate()
    if not llm_base_url:
        llm_base_url = vllm.LLM_BASE_URL
    asyncio.run(check_llm.execute(llm_base_url, model_id))


@node_app.command("benchmark", help="Benchmarks the node")
def benchmark(
    model_id: str = typer.Option(config.GALADRIEL_MODEL_ID, help="Model ID"),
    llm_base_url: Optional[str] = typer.Option(
        config.GALADRIEL_LLM_BASE_URL, help="LLM base url"
    ),
    concurrency: int = typer.Option(2, help="How many concurrent requests"),
    requests: int = typer.Option(10, help="How many requests per worker"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    init_logging(debug)
    config.validate()
    if not llm_base_url:
        llm_base_url = vllm.LLM_BASE_URL
    asyncio.run(long_benchmark.execute(llm_base_url, model_id, concurrency, requests))


@node_app.command("stats", help="Get node stats")
def node_stats(
    api_url: str = typer.Option(config.GALADRIEL_API_URL, help="API url"),
    api_key: str = typer.Option(config.GALADRIEL_API_KEY, help="API key"),
    node_id: str = typer.Option(config.GALADRIEL_NODE_ID, help="Node ID"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    init_logging(debug)
    config.validate()
    status, response_json = asyncio.run(
        version_aware_get(
            api_url, "node/stats", api_key, query_params={"node_id": node_id}
        )
    )
    if status == HTTPStatus.OK and response_json:
        rich.print("Received stats:")
        excluded_keys = ["completed_inferences"]
        for k, v in response_json.items():
            if k not in excluded_keys:
                rich.print(f"{k}: {v if v is not None else '<UNKNOWN>'}", flush=True)
        if response_json.get("completed_inferences"):
            rich.print("Latest completed inferences:", flush=True)
        for i in response_json.get("completed_inferences", []):
            rich.print(i, flush=True)


@node_app.command("upgrade", help="Upgrade the node to the latest version")
def node_upgrade(
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    init_logging(debug)
    try:
        logger.info("Updating galadriel CLI to the latest version...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "galadriel-node"]
        )
        logger.info(
            "galadriel CLI has been successfully updated to the latest version."
        )
    except subprocess.CalledProcessError:
        logger.info(
            "An error occurred while updating galadriel CLI. Please check your internet connection and try again.",
        )
    except Exception as _:
        logger.error("An unexpected error occurred.", exc_info=True)


if __name__ == "__main__":
    try:
        init_logging(True)
        asyncio.run(
            run_node.execute(
                config.GALADRIEL_API_URL,
                config.GALADRIEL_RPC_URL,
                config.GALADRIEL_API_KEY,
                config.GALADRIEL_NODE_ID,
                config.GALADRIEL_LLM_BASE_URL,
            )
        )
    except SdkError as e:
        logger.error("Got an Exception when trying to run the node.", exc_info=True)
    except Exception as e:
        logger.error(
            "Got an unexpected Exception when trying to run the node.", exc_info=True
        )

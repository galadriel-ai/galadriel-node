import asyncio
import importlib.resources
import json
import time
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import Dict
from typing import List
from typing import Optional
from urllib.parse import urljoin

import aiohttp
from openai.types.chat import ChatCompletionChunk

from galadriel_node.config import config
from galadriel_node.sdk import api
from galadriel_node.sdk.entities import AuthenticationError
from galadriel_node.sdk.entities import SdkError
from galadriel_node.sdk.llm import Llm
from galadriel_node.sdk.protocol.entities import InferenceRequest
from galadriel_node.sdk.protocol.entities import InferenceStatusCodes
from galadriel_node.sdk.system.report_hardware import logger

BENCHMARK_TIME_SECONDS = 60
NUM_THREADS = 16
BASE_REQUEST = {
    "model": config.GALADRIEL_MODEL_ID,
    "temperature": 0,
    "seed": 123,
    "stream": True,
    "stream_options": {"include_usage": True},
    "max_tokens": 1000,
}


async def report_performance(
    api_url: str,
    api_key: str,
    node_id: str,
    llm_base_url: str,
    model_name: str,
) -> None:
    existing_tokens_per_second = await _get_benchmark(
        model_name, api_url, api_key, node_id
    )
    if existing_tokens_per_second:
        min_tokens_per_sec = config.MINIMUM_COMPLETIONS_TOKENS_PER_SECOND_PER_MODEL.get(
            model_name, config.MINIMUM_COMPLETIONS_TOKENS_PER_SECOND
        )
        if existing_tokens_per_second > min_tokens_per_sec:
            logger.info("Node benchmarking is already done")
            return None
        logger.info("Node benchmarking results are too low, retrying")

    tokens_per_sec = await _get_benchmark_tokens_per_sec(llm_base_url)
    await _post_benchmark(model_name, tokens_per_sec, api_url, api_key, node_id)


async def _get_benchmark(
    model_name: str, api_url: str, api_key: str, node_id: str
) -> Optional[float]:
    query_params = {"model": model_name, "node_id": node_id}
    response_status, response_json = await api.get(
        api_url, "node/benchmark", api_key, query_params
    )
    if response_status != 200:
        return None
    return response_json.get("tokens_per_second")


async def _get_benchmark_tokens_per_sec(llm_base_url: str) -> float:
    logger.info("Starting LLM benchmarking...")
    logger.info("    Loading prompts dataset")
    dataset: List[Dict] = _load_dataset()

    logger.info("    Using %d threads", NUM_THREADS)
    logger.info(
        "    Running inference requests, this will take around %d seconds...",
        BENCHMARK_TIME_SECONDS,
    )
    llm = Llm(llm_base_url)
    datasets = _split_dataset(dataset, NUM_THREADS)
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        benchmark_start = time.time()
        tasks = [
            loop.run_in_executor(executor, _run_llm, benchmark_start, datasets[i], llm)
            for i in range(NUM_THREADS)
        ]
        results = await asyncio.gather(*tasks)
        benchmark_end = time.time()

    completion_tokens_all_threads = sum(results)
    time_elapsed = benchmark_end - benchmark_start
    tokens_per_sec = completion_tokens_all_threads / time_elapsed
    logger.info("    Benchmarking done!")
    logger.info("    Time elapsed: %s", time_elapsed)
    logger.info("    Average tokens/sec: %s", tokens_per_sec)
    return tokens_per_sec


def _load_dataset() -> List[Dict]:
    with importlib.resources.files("galadriel_node.sdk.datasets").joinpath(
        "im_feeling_curious.jsonl"
    ).open("r", encoding="utf-8") as json_file:
        json_list = list(json_file)

    results = []
    for json_str in json_list:
        results.append(json.loads(json_str))
    return results


def _split_dataset(lst, n):
    avg = int(len(lst) / n)
    # Split list, last partition take all remaining elements
    return [lst[i * avg : (i + 1) * avg if i + 1 < n else None] for i in range(n)]


def _run_llm(benchmark_start: float, dataset: List[Dict], llm: Llm) -> int:
    i = 0
    completion_tokens = 0
    while time.time() - benchmark_start < BENCHMARK_TIME_SECONDS:
        request_data = {**BASE_REQUEST, "messages": [dataset[i]["chat"][0]]}
        request = InferenceRequest(id="test", chat_request=request_data)
        tokens = asyncio.run(_make_inference_request(benchmark_start, llm, request))
        completion_tokens += tokens
        i += 1
    return completion_tokens


def _check_if_inference_done(chunk: ChatCompletionChunk) -> bool:
    return not chunk.choices or (
        len(chunk.choices) == 1
        and chunk.choices[0].delta.content == ""
        and chunk.choices[0].finish_reason is not None
    )


async def _make_inference_request(
    benchmark_start: float,
    llm: Llm,
    request: InferenceRequest,
) -> int:
    completion_tokens = None
    async for chunk in llm.execute(request, is_benchmark=True):
        if chunk.status == InferenceStatusCodes.ERROR:
            raise SdkError(
                "Failed to call LLM, make sure GALADRIEL_LLM_BASE_URL is correct"
            )
        if chunk.chunk and chunk.chunk.usage:
            completion_tokens = chunk.chunk.usage.completion_tokens
        if chunk.status == InferenceStatusCodes.DONE:
            if completion_tokens is not None:
                return completion_tokens
            raise SdkError("Unexpected error: No usage data available")
        # yield to the event loop to allow checking time elapsed
        await asyncio.sleep(0)
        if time.time() - benchmark_start > BENCHMARK_TIME_SECONDS:
            if completion_tokens is not None:
                return completion_tokens
            break
    logger.info("        Request failed")
    return 0


async def _post_benchmark(
    model_name: str,
    tokens_per_sec: float,
    api_url: str,
    api_key: str,
    node_id: str,
) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            urljoin(api_url + "/", "node/benchmark"),
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "node_id": node_id,
                "model_name": model_name,
                "tokens_per_second": tokens_per_sec,
            },
        ) as response:
            await response.json()
            if response.status == HTTPStatus.OK:
                logger.info("Successfully sent benchmark results")
            elif response.status == HTTPStatus.UNAUTHORIZED:
                raise AuthenticationError("Unauthorized to save benchmark results")
            else:
                raise SdkError("Failed to save benchmark results")


if __name__ == "__main__":
    asyncio.run(_get_benchmark_tokens_per_sec("http://localhost:11434"))

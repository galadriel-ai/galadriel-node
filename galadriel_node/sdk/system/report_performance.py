import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from typing import List

from galadriel_node.config import config
from galadriel_node.sdk.entities import InferenceRequest
from galadriel_node.sdk.llm import Llm

# TODO: update
BENCHMARK_TIME_SECONDS = 20
BASE_REQUEST = {
    "model": config.GALADRIEL_MODEL_ID,
    "temperature": 0,
    "seed": 123,
    "stream": True,
    "stream_options": {
        "include_usage": True
    },
    "max_tokens": 1000
}


async def report_performance(llm_base_url: str) -> None:
    # TODO: check if this is required etc
    tokens_per_sec = await _get_benchmark_tokens_per_sec(llm_base_url)


async def _get_benchmark_tokens_per_sec(llm_base_url: str) -> int:
    print("Starting LLM benchmarking...", flush=True)
    print("    Loading prompts dataset", flush=True)
    dataset: List[Dict] = _load_dataset()

    print(f"    Running inference, this will take around {BENCHMARK_TIME_SECONDS}seconds", flush=True)

    llm = Llm()
    num_threads = 3
    datasets = _split_dataset(dataset, num_threads)
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        benchmark_start = time.time()
        tasks = [
            loop.run_in_executor(executor, _run_llm, benchmark_start, datasets[i], llm, llm_base_url)
            for i in range(num_threads)
        ]
        results = await asyncio.gather(*tasks)
        benchmark_end = time.time()

    total_tokens_all_threads = sum(results)
    time_elapsed = benchmark_end - benchmark_start
    tokens_per_sec = total_tokens_all_threads / time_elapsed
    print(f"tokens_per_sec: {tokens_per_sec}")
    print(f"time elapsed: {time_elapsed}")
    return tokens_per_sec


def _load_dataset() -> List[Dict]:
    with open("./galadriel_node/sdk/datasets/im_feeling_curious.jsonl", "r") as json_file:
        json_list = list(json_file)

    results = []
    for json_str in json_list:
        results.append(json.loads(json_str))
    return results


def _split_dataset(lst, n):
    avg = int(len(lst) / n)
    # Split list, last partition take all remaining elements
    return [lst[i * avg:(i + 1) * avg if i + 1 < n else None] for i in range(n)]


def _run_llm(benchmark_start: float, dataset: List[Dict], llm: Llm, llm_base_url: str) -> int:
    i = 0
    total_tokens = 0
    while time.time() - benchmark_start < BENCHMARK_TIME_SECONDS:
        request_data = {
            **BASE_REQUEST,
            "messages": dataset[i]["chat"]
        }
        request = InferenceRequest(
            id="test",
            chat_request=request_data
        )
        tokens = asyncio.run(_make_inference_request(benchmark_start, llm, request, llm_base_url))
        total_tokens += tokens
        i += 1
    return total_tokens


async def _make_inference_request(
    benchmark_start: float,
    llm: Llm,
    request: InferenceRequest,
    llm_base_url: str,
) -> int:
    async for chunk in llm.execute(request, llm_base_url, is_benchmark=True):
        chunk_data = chunk.chunk
        if not len(chunk_data.choices) and chunk_data.usage and chunk_data.usage.total_tokens:
            return chunk_data.usage.total_tokens
        if time.time() - benchmark_start < BENCHMARK_TIME_SECONDS:
            if chunk_data.usage and chunk_data.usage.total_tokens:
                return chunk_data.usage.total_tokens
            break
    print("        Request failed")
    return 0

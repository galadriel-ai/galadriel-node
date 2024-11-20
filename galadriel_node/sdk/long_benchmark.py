import importlib.resources
from typing import List
from urllib.parse import urljoin

import openai

from galadriel_node.sdk.logging_utils import get_node_logger
from galadriel_node.sdk.protocol.entities import InferenceRequest
from galadriel_node.sdk.time_tracker import TimeTracker

logger = get_node_logger()

BENCHMARK_COUNT = 10


async def execute(llm_base_url: str, model_id: str) -> None:
    trackers = []
    for _ in range(BENCHMARK_COUNT):
        tracker = await _run_inference(llm_base_url, model_id)
        print("\nResults:")
        print("  prompt_tokens:", tracker.get_prompt_tokens())
        print("  time_to_first_token:", tracker.get_time_to_first_token())
        print("  total_time:", tracker.get_total_time())
        trackers.append(tracker)

    _print_final_results(trackers)


async def _run_inference(llm_base_url: str, model_id: str) -> TimeTracker:
    text = _get_text()
    base_url: str = urljoin(llm_base_url, "/v1")
    client = openai.AsyncOpenAI(base_url=base_url, api_key="sk-no-key-required")
    request = InferenceRequest(
        id="mock_id",
        chat_request={
            "model": model_id,
            "messages": [
                {"content": "You are a helpful assistant.", "role": "system"},
                {"content": text, "role": "user"},
            ],
            "max_tokens": 1,
        },
    )
    request.chat_request["stream"] = True
    request.chat_request["stream_options"] = {"include_usage": True}
    tracker = TimeTracker()
    tracker.start()
    try:
        completion = await client.chat.completions.create(**request.chat_request)
        async for chunk in completion:
            tracker.chunk_received(chunk)
    except openai.APIStatusError as exc:
        print("EXC:", exc)
    except Exception as exc:
        print("EXC:", exc)

    return tracker


def _get_text():
    with importlib.resources.files("galadriel_node.sdk.datasets").joinpath(
        "ai_wiki_8k.txt"
    ).open("r", encoding="utf-8") as file:
        return file.read()


def _print_final_results(trackers: List[TimeTracker]) -> None:
    ttfts = []
    for tracker in trackers:
        ttfts.append(tracker.get_time_to_first_token())

    print("\nFinal Result:")
    print("  min:", min(ttfts))
    print("  max:", max(ttfts))
    print("  avg:", sum(ttfts) / len(ttfts))

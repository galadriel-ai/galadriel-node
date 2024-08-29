from typing import AsyncGenerator
from urllib.parse import urljoin

import openai

from galadriel_node.sdk.entities import InferenceRequest
from galadriel_node.sdk.entities import InferenceResponse


class Llm:
    async def execute(
        self, request: InferenceRequest, inference_base_url: str
    ) -> AsyncGenerator[InferenceResponse, None]:
        print(f"Running inference, id={request.id}", flush=True)
        base_url: str = urljoin(inference_base_url, "/v1")
        client = openai.AsyncOpenAI(base_url=base_url, api_key="sk-no-key-required")
        # Force streaming and token usage inclusion
        request.chat_request["stream"] = True
        request.chat_request["stream_options"] = {
            "include_usage": True
        }
        try:
            completion = await client.chat.completions.create(**request.chat_request)
            async for chunk in completion:
                yield InferenceResponse(
                    request_id=request.id,
                    chunk=chunk,
                )
        except Exception as exc:
            print(exc)


def _get_messages_dict(request: InferenceRequest):
    return [{"role": i.role, "content": i.content.value} for i in request.messages]


if __name__ == "__main__":
    ollama = Llm()
    # from galadriel_node.sdk.entities import InferenceRunStatus
    # r = ollama.execute(InferenceRun(
    #     id="id",
    #     prompt="hi",
    #     model_id="llama3",
    #     selected_gpu_nodes=[],
    #     status=InferenceRunStatus.COMMIT,
    #     start_block=0,
    #     history=[],
    # ))
    r = ollama.get_model_hash("llama3")
    print("Response:", r)

from typing import AsyncGenerator
from urllib.parse import urljoin

import openai

from galadriel_node.sdk.entities import InferenceRequest
from galadriel_node.sdk.entities import InferenceResponse


class Llm:
    async def execute(
        self, request: InferenceRequest, inference_base_url: str
    ) -> AsyncGenerator[InferenceResponse, None]:
        base_url: str = urljoin(inference_base_url, "/v1")
        client = openai.AsyncOpenAI(base_url=base_url, api_key="sk-no-key-required")
        try:
            messages = _get_messages_dict(request)
            completion = await client.chat.completions.create(
                model=request.model,
                temperature=0,
                messages=messages,
                stream=True,
            )
            async for chunk in completion:
                yield InferenceResponse(
                    request_id=request.id,
                    content=chunk.choices[0].delta.content or "",
                    finish_reason=chunk.choices[0].finish_reason,
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

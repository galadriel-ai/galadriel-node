from typing import AsyncGenerator
from urllib.parse import urljoin

import openai

from galadriel_node.sdk.entities import InferenceError
from galadriel_node.sdk.entities import InferenceRequest
from galadriel_node.sdk.entities import InferenceResponse
from galadriel_node.sdk.entities import InferenceStatusCodes


# pylint: disable=R0903
class Llm:
    async def execute(
        self,
        request: InferenceRequest,
        inference_base_url: str,
        is_benchmark: bool = False,
    ) -> AsyncGenerator[InferenceResponse, None]:
        if not is_benchmark:
            print(f"Running inference, id={request.id}", flush=True)
        base_url: str = urljoin(inference_base_url, "/v1")
        client = openai.AsyncOpenAI(base_url=base_url, api_key="sk-no-key-required")
        # Force streaming and token usage inclusion
        request.chat_request["stream"] = True
        request.chat_request["stream_options"] = {"include_usage": True}
        try:
            completion = await client.chat.completions.create(**request.chat_request)
            async for chunk in completion:
                yield InferenceResponse(
                    request_id=request.id,
                    chunk=chunk,
                )
        except openai.APIStatusError as exc:
            yield InferenceResponse(
                request_id=request.id,
                error=InferenceError(
                    status_code=InferenceStatusCodes(exc.status_code),
                    message=str(exc),
                ),
            )
        except Exception as exc:
            yield InferenceResponse(
                request_id=request.id,
                error=InferenceError(
                    status_code=InferenceStatusCodes.UNKNOWN_ERROR,
                    message=str(exc),
                ),
            )

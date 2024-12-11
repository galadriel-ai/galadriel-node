from urllib.parse import urljoin

import openai


async def execute(
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

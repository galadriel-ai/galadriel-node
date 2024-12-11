import aiohttp


async def execute(llm_base_url: str, total_timeout: float = 60.0):
    timeout = aiohttp.ClientTimeout(total=total_timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        return await session.get(llm_base_url + "/v1/models/")

from unittest.mock import AsyncMock

from galadriel_node.sdk.jobs.api_ping_job import ApiPingJob


async def test_api_ping_job():
    domain = "api.galadriel.com"
    api_ping_job = ApiPingJob(domain)
    api_ping_job._check_api_ping_time = AsyncMock()

    assert api_ping_job.domain == domain
    assert api_ping_job.ping_time == []
    assert api_ping_job._lock

    await api_ping_job._append_ping_time(None)
    await api_ping_job._append_ping_time(100)

    assert await api_ping_job.get_and_clear_ping_time() == [None, 100]
    assert await api_ping_job.get_and_clear_ping_time() == []

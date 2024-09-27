import pytest
from unittest.mock import MagicMock, patch
from http import HTTPStatus
from galadriel_node.config import config
from galadriel_node.sdk.entities import AuthenticationError, SdkError
from galadriel_node.sdk.system.report_hardware import _post_info
from galadriel_node.sdk.system.report_hardware import report_hardware


class MockResponse:
    def __init__(self, json, status):
        self._json = json
        self.status = status

    async def json(self):
        return self._json

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


async def test_post_info_unauthorized():
    with patch(
        "aiohttp.ClientSession.post",
        return_value=MockResponse({}, HTTPStatus.UNAUTHORIZED),
    ) as mock_session:
        with pytest.raises(
            AuthenticationError, match="Unauthorized to send hardware info"
        ):
            await _post_info(
                MagicMock(), "mock_api_url", "mock_api_key", "mock_node_id"
            )


async def test_post_info_network_speed():
    mock_node_info = MagicMock()
    mock_node_info.network_download_speed = 15.5
    mock_node_info.network_upload_speed = 12.3

    with patch(
        "aiohttp.ClientSession.post",
        return_value=MockResponse({"message": "Hardware info saved"}, HTTPStatus.OK),
    ) as mock_post:
        await _post_info(mock_node_info, "mock_api_url", "mock_api_key", "mock_node_id")

        # Check if the post request was made with the correct data
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert "json" in kwargs
        assert kwargs["json"]["network_download_speed"] == 15.5
        assert kwargs["json"]["network_upload_speed"] == 12.3


@pytest.mark.parametrize(
    "download_speed, upload_speed, expected_result",
    [
        (9, 10, False),  # Download speed below MIN_DOWNLOAD_SPEED
        (10, 9, False),  # Upload speed below MIN_UPLOAD_SPEED
        (9, 9, False),  # Both speeds below minimum
        (10, 10, True),  # Both speeds at minimum
        (11, 11, True),  # Both speeds above minimum
    ],
)
def test_get_network_speed(monkeypatch, download_speed, upload_speed, expected_result):
    # Mock the speedtest.Speedtest class
    class MockSpeedtest:
        def download(self):
            return download_speed

        def upload(self):
            return upload_speed

    monkeypatch.setattr("speedtest.Speedtest", MockSpeedtest)

    # Import the function here to ensure the monkeypatch is applied
    from galadriel_node.sdk.system.report_hardware import _get_network_speed

    if expected_result:
        assert _get_network_speed() == (download_speed, upload_speed)
    else:
        with pytest.raises(
            SdkError, match="Network speed is too slow to run Galadriel."
        ):
            _get_network_speed()


@pytest.mark.asyncio
async def test_report_hardware_update_slow_network(monkeypatch):
    # Mock _get_info_already_exists to return False
    async def mock_get_info_already_exists(*args, **kwargs):
        return False

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware._get_info_already_exists",
        mock_get_info_already_exists,
    )

    # Mock get_gpu_info
    def mock_get_gpu_info():
        return "NVIDIA GeForce RTX 3090", 24576

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware.get_gpu_info", mock_get_gpu_info
    )

    # Mock _get_cpu_info
    def mock_get_cpu_info():
        return "Intel Core i9-10900K", 10

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware._get_cpu_info", mock_get_cpu_info
    )

    # Mock _get_ram
    def mock_get_ram():
        return 32768

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware._get_ram", mock_get_ram
    )

    # Mock _get_network_speed to return speeds below minimum
    def mock_get_network_speed():
        return 9.0, 9.0

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware._get_network_speed",
        mock_get_network_speed,
    )

    # Call report_hardware and expect SdkError
    config.GALADRIEL_ENVIRONMENT = "production"
    with pytest.raises(SdkError, match="Network speed is too slow to run Galadriel."):
        await report_hardware("mock_api_url", "mock_api_key", "mock_node_id")


@pytest.mark.asyncio
async def test_report_hardware_success(monkeypatch):
    gpu_name = "NVIDIA GeForce RTX 3090"
    vram = 24576
    cpu_model = "Intel(R) Core(TM) i9-10900K CPU @ 3.70GHz"
    cpu_count = 10
    ram = 32768
    network_download_speed = 100.0
    network_upload_speed = 100.0
    operating_system = "Linux-5.4.0-42-generic-x86_64-with-glibc2.29"

    # Mock _get_info_already_exists
    async def mock_get_info_already_exists(*args, **kwargs):
        return False

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware._get_info_already_exists",
        mock_get_info_already_exists,
    )

    # Mock get_gpu_info
    def mock_get_gpu_info():
        return gpu_name, vram

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware.get_gpu_info", mock_get_gpu_info
    )

    # Mock _get_cpu_info
    def mock_get_cpu_info():
        return cpu_model, cpu_count

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware._get_cpu_info", mock_get_cpu_info
    )

    # Mock _get_ram
    def mock_get_ram():
        return ram

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware._get_ram", mock_get_ram
    )

    # Mock _get_network_speed
    def mock_get_network_speed():
        return network_download_speed, network_upload_speed

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware._get_network_speed",
        mock_get_network_speed,
    )

    # Mock _post_info
    async def mock_post_info(node_info, api_url, api_key, node_id):
        if not (
            node_info.gpu_model == gpu_name
            and node_info.vram == vram
            and node_info.cpu_model == cpu_model
            and node_info.cpu_count == cpu_count
            and node_info.ram == ram
            and node_info.network_download_speed == network_download_speed
            and node_info.network_upload_speed == network_upload_speed
            and node_info.operating_system == operating_system
        ):
            raise Exception("Incorrect node info")

    monkeypatch.setattr(
        "galadriel_node.sdk.system.report_hardware._post_info", mock_post_info
    )

    # Mock platform.platform()
    def mock_platform():
        return operating_system

    monkeypatch.setattr("platform.platform", mock_platform)

    # Call report_hardware and expect no exceptions
    try:
        config.GALADRIEL_ENVIRONMENT = "production"
        await report_hardware("mock_api_url", "mock_api_key", "mock_node_id")
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")

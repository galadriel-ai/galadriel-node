from dataclasses import dataclass

import platform
from http import HTTPStatus
from typing import Tuple
from urllib.parse import urljoin


import importlib
import aiohttp
import cpuinfo
import psutil
import speedtest
from gpustat import GPUStatCollection

from galadriel_node.config import config
from galadriel_node.sdk import api
from galadriel_node.sdk.entities import SdkError
from galadriel_node.sdk.entities import AuthenticationError
from galadriel_node.sdk.system.entities import GPUInfo
from galadriel_node.sdk.system.entities import NodeInfo

MIN_CPU_CORES = 2
MIN_RAM_MB = 2048
SUPPORTED_GPUS = [
    # TODO: add more
    "NVIDIA GeForce RTX 4090",
    "NVIDIA GeForce RTX 3090",
]
MIN_DOWNLOAD_SPEED = 10  # MB/s
MIN_UPLOAD_SPEED = 10  # MB/s


async def report_hardware(api_url: str, api_key: str, node_id: str) -> None:
    if await _get_info_already_exists(api_url, api_key, node_id):
        print("Node info is already saved", flush=True)
        return None
    if config.GALADRIEL_ENVIRONMENT == "local":
        version = _get_version()
        node_info = NodeInfo(
            gpu_model=SUPPORTED_GPUS[0],
            gpu_count=1,
            vram=20000,
            cpu_model="macOS-14.4.1-arm64-arm-64bit",
            cpu_count=8,
            ram=16384,
            network_download_speed=100,
            network_upload_speed=100,
            operating_system="macOS-14.4.1-arm64-arm-64bit",
            version=version,
        )
    else:
        gpu_info = get_gpu_info()
        cpu_model, cpu_count = _get_cpu_info()
        if cpu_count < MIN_CPU_CORES:
            raise SdkError(f"Not enough CPU cores, minimum {MIN_CPU_CORES} required")
        total_mem_mb = _get_ram()
        if total_mem_mb < MIN_RAM_MB:
            raise SdkError(f"Not enough RAM, minimum {MIN_RAM_MB}MB required")
        download_speed_mbs, upload_speed_mbs = _get_network_speed()
        if (
            download_speed_mbs < MIN_DOWNLOAD_SPEED
            or upload_speed_mbs < MIN_UPLOAD_SPEED
        ):
            raise SdkError("Network speed is too slow to run Galadriel.")
        version = _get_version()

        node_info = NodeInfo(
            gpu_model=gpu_info.gpu_model,
            vram=gpu_info.vram,
            gpu_count=gpu_info.gpu_count,
            cpu_model=cpu_model,
            cpu_count=cpu_count,
            ram=total_mem_mb,
            network_download_speed=download_speed_mbs,
            network_upload_speed=upload_speed_mbs,
            operating_system=platform.platform(),
            version=version,
        )
    await _post_info(node_info, api_url, api_key, node_id)


def get_gpu_info() -> GPUInfo:
    try:
        query = GPUStatCollection.new_query()
        data = query.jsonify()
    except Exception:
        raise SdkError(
            "No supported GPU found, make sure `nvidia-smi` works, NVIDIA driver versions must be R450.00 or higher."
        )

    if not data["gpus"]:
        raise SdkError(
            "No supported GPU found, make sure you have a supported NVIDIA GPU."
        )

    gpus = [gpu for gpu in data["gpus"] if "NVIDIA" in gpu["name"]]
    if not gpus:
        raise SdkError(
            "No supported GPU found, make sure you have a supported NVIDIA GPU."
        )

    gpu_name = gpus[0]["name"]
    gpu_vram_mb = gpus[0]["memory.total"] * 1.048576
    gpu_count = len(gpus)

    return GPUInfo(gpu_model=gpu_name, vram=int(gpu_vram_mb), gpu_count=gpu_count)


def _get_cpu_info() -> Tuple[str, int]:
    cpu_name = cpuinfo.get_cpu_info()["brand_raw"]
    cpu_count = psutil.cpu_count(logical=False)
    return cpu_name, cpu_count


def _get_ram() -> int:
    mem = psutil.virtual_memory()
    total_mem_mb = int(mem.total / (1024**2))
    return total_mem_mb


def _get_network_speed() -> Tuple[float, float]:
    st = speedtest.Speedtest()
    print("Testing download speed..", flush=True)
    download_speed_mbs = round(st.download() / 1_000_000, 2)
    print("Testing upload speed..", flush=True)
    upload_speed_mbs = round(st.upload() / 1_000_000, 2)
    return download_speed_mbs, upload_speed_mbs


def _get_version() -> str:
    return importlib.metadata.version("galadriel-node")


async def _get_info_already_exists(api_url: str, api_key: str, node_id: str) -> bool:
    response_status, response_json = await api.get(
        api_url, "node/info", api_key, query_params={"node_id": node_id}
    )
    if response_status != HTTPStatus.OK:
        return False
    download_speed = response_json.get("network_download_speed")
    upload_speed = response_json.get("network_upload_speed")
    # This is to force already saved nodes to run the check again if
    # the speed is not enough.
    if download_speed is not None and download_speed < MIN_DOWNLOAD_SPEED:
        return False
    if upload_speed is not None and upload_speed < MIN_UPLOAD_SPEED:
        return False
    if response_json.get("version") != _get_version():
        return False
    return (
        response_json.get("gpu_model") is not None
        and response_json.get("cpu_model") is not None
        and response_json.get("gpu_count") is not None
    )


async def _post_info(
    node_info: NodeInfo, api_url: str, api_key: str, node_id: str
) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            urljoin(api_url + "/", "node/info"),
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "node_id": node_id,
                "gpu_model": node_info.gpu_model,
                "vram": node_info.vram,
                "gpu_count": node_info.gpu_count,
                "cpu_model": node_info.cpu_model,
                "cpu_count": node_info.cpu_count,
                "ram": node_info.ram,
                "network_download_speed": node_info.network_download_speed,
                "network_upload_speed": node_info.network_upload_speed,
                "operating_system": node_info.operating_system,
                "version": node_info.version,
            },
        ) as response:
            await response.json()
            if response.status == HTTPStatus.OK:
                print("Successfully sent hardware info", flush=True)
            elif response.status == HTTPStatus.UNAUTHORIZED:
                raise AuthenticationError("Unauthorized to send hardware info")
            else:
                raise SdkError("Failed to save hardware info")

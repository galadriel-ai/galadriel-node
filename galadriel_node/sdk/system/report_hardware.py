import platform
from typing import Tuple
from urllib.parse import urljoin

import aiohttp
import cpuinfo
import psutil
import speedtest
from gpustat import GPUStatCollection

from galadriel_node.config import config
from galadriel_node.sdk import api
from galadriel_node.sdk.entities import SdkError
from galadriel_node.sdk.system.entities import NodeInfo

MIN_CPU_CORES = 2
MIN_RAM_MB = 2048
SUPPORTED_GPUS = [
    # TODO: add more
    "NVIDIA GeForce RTX 4090",
    "NVIDIA GeForce RTX 3090",
]


async def report_hardware(api_url: str, api_key: str) -> None:
    if await _get_info(api_url, api_key):
        print("Node info is already saved", flush=True)
        return None
    if config.GALADRIEL_ENVIRONMENT == "local":
        node_info = NodeInfo(
            gpu_model=SUPPORTED_GPUS[0],
            vram=20000,
            cpu_model="macOS-14.4.1-arm64-arm-64bit",
            cpu_count=8,
            ram=16384,
            network_download_speed=100,
            network_upload_speed=100,
            operating_system="macOS-14.4.1-arm64-arm-64bit",
        )
    else:
        gpu_name, gpu_vram_mb = _get_gpu_info()
        cpu_model, cpu_count = _get_cpu_info()
        if cpu_count < MIN_CPU_CORES:
            raise SdkError(f"Not enough CPU cores, minimum {MIN_CPU_CORES} required")
        total_mem_mb = _get_ram()
        if total_mem_mb < MIN_RAM_MB:
            raise SdkError(f"Not enough RAM, minimum {MIN_RAM_MB}MB required")
        download_speed_mbs, upload_speed_mbs = _get_network_speed()

        node_info = NodeInfo(
            gpu_model=gpu_name,
            vram=gpu_vram_mb,
            cpu_model=cpu_model,
            cpu_count=cpu_count,
            ram=total_mem_mb,
            network_download_speed=download_speed_mbs,
            network_upload_speed=upload_speed_mbs,
            operating_system=platform.platform(),
        )
    await _post_info(node_info, api_url, api_key)


def _get_gpu_info() -> Tuple[str, int]:
    try:
        query = GPUStatCollection.new_query()
        data = query.jsonify()
    except Exception as e:
        raise SdkError(
            "No supported GPU found, make sure `nvidia-smi` works, NVIDIA driver versions must be R450.00 or higher."
        )

    if not len(data["gpus"]):
        raise SdkError(
            "No supported GPU found, make sure you have a supported NVIDIA GPU."
        )
    for gpu in data["gpus"]:
        if gpu["name"] in SUPPORTED_GPUS:
            gpu_name = gpu["name"]
            gpu_vram_mb = gpu["memory.total"] * 1.048576
            return gpu_name, int(gpu_vram_mb)
    raise SdkError("No supported GPU found, make sure you have a supported NVIDIA GPU.")


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


async def _get_info(api_url: str, api_key: str):
    response_status, _ = await api.get(api_url, "node/info", api_key)
    return response_status == 200


async def _post_info(node_info: NodeInfo, api_url: str, api_key: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            urljoin(api_url + "/", "node/info"),
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "gpu_model": node_info.gpu_model,
                "vram": node_info.vram,
                "cpu_model": node_info.cpu_model,
                "cpu_count": node_info.cpu_count,
                "ram": node_info.ram,
                "network_download_speed": node_info.network_download_speed,
                "network_upload_speed": node_info.network_upload_speed,
                "operating_system": node_info.operating_system,
            },
        ) as response:
            await response.json()
            if response.status == 200:
                print("Successfully sent hardware info", flush=True)
            else:
                raise SdkError("Failed to save hardware info")

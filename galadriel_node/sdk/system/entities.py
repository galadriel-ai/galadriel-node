from typing import List
from dataclasses import dataclass


@dataclass
class GPUInfo:
    gpu_model: str
    vram: int
    gpu_count: int
    power_limit: int


@dataclass
class NodeInfo(GPUInfo):
    cpu_model: str
    cpu_count: int
    ram: int
    network_download_speed: float
    network_upload_speed: float
    operating_system: str
    version: str


@dataclass
class GPUUtilization:
    gpu_percent: int
    vram_percent: int
    power_percent: int


@dataclass
class NodeUtilization:
    cpu_percent: int
    ram_percent: int
    disk_percent: int
    gpus: List[GPUUtilization]

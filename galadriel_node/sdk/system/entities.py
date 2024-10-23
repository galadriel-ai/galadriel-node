from typing import List
from dataclasses import dataclass


@dataclass
class NodeInfo:
    gpu_model: str
    vram: int
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


@dataclass
class NodeUtilization:
    cpu_percent: int
    ram_percent: int
    disk_percent: int
    gpus: List[GPUUtilization]

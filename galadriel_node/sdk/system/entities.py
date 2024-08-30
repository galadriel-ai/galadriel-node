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

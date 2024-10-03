from typing import Tuple

from gpustat import GPUStatCollection

from galadriel_node.sdk.entities import SdkError


def get_gpu_info() -> Tuple[str, int]:
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
    for gpu in data["gpus"]:
        if "NVIDIA" in gpu["name"]:
            gpu_name = gpu["name"]
            gpu_vram_mb = gpu["memory.total"] * 1.048576
            return gpu_name, int(gpu_vram_mb)
    raise SdkError("No supported GPU found, make sure you have a supported NVIDIA GPU.")

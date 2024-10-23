import os

import psutil

from gpustat import GPUStatCollection
from galadriel_node.sdk.system.entities import GPUUtilization
from galadriel_node.sdk.system.entities import NodeUtilization


async def execute() -> NodeUtilization:
    cpu_usage = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    query = GPUStatCollection.new_query()
    return NodeUtilization(
        cpu_percent=round(cpu_usage),
        ram_percent=round(mem.percent),
        disk_percent=round(psutil.disk_usage(current_dir).percent),
        gpus=[
            GPUUtilization(
                gpu_percent=gpu.utilization,
                vram_percent=round(gpu.memory_used / gpu.memory_total * 100),
            )
            for gpu in query.gpus
        ],
    )

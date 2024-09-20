import importlib.metadata
import os
import subprocess
from typing import Optional

import psutil

from galadriel_node.sdk.system.report_hardware import get_gpu_info

CONTEXT_SIZE = 8192
LLM_BASE_URL = "http://127.0.0.1:19434"


def is_installed() -> bool:
    try:
        importlib.metadata.version("vllm")
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def is_running(model_name: str) -> bool:
    for process in psutil.process_iter():
        try:
            cmdline = process.cmdline()
            if any(os.path.basename(arg).startswith("python") for arg in cmdline):
                for i in range(len(cmdline) - 2):
                    if os.path.basename(cmdline[i]) == "vllm" and cmdline[
                        i + 1 : i + 3
                    ] == ["serve", model_name]:
                        return True
        except (psutil.NoSuchProcess, IndexError):
            pass
    return False


def is_process_running(pid: int) -> bool:
    """Check if a process with a given PID is still running."""
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


def stop(pid: int) -> bool:
    try:
        process = psutil.Process(pid)
        process.kill()
        process.wait(timeout=2)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
        print(f"Failed to forcibly kill process with PID {pid}: {e}")
        return False


# pylint: disable=R1732
def start(model_name: str, debug: bool = False) -> Optional[int]:
    _, gpu_vram_mb = get_gpu_info()
    try:
        command = [
            "vllm",
            "serve",
            model_name,
            "--max-model-len",
            "8192",
            "--gpu-memory-utilization",
            "1",
            "--host",
            "127.0.0.1",
            "--port",
            "19434",
            "--disable-frontend-multiprocessing",
        ]
        if gpu_vram_mb <= 8192:
            command.extend(
                [
                    "--kv_cache_dtype",
                    "fp8",
                    "--max_num_seqs",
                    "128",
                    "--max_num_batched_tokens",
                    "8192",
                ]
            )
        with open("vllm.log", "a", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                command, stdout=log_file, stderr=log_file, start_new_session=True
            )
            if debug:
                print(
                    f'Started vllm process with PID: {process.pid}, logging to "vllm.log"'
                )
            return process.pid
    except Exception as e:
        if debug:
            print(f"Error starting vllm process: {e}")
        return None

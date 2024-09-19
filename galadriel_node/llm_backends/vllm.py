import importlib.metadata
import os
import subprocess

import psutil

from galadriel_node.sdk.system.entities import NodeInfo

CONTEXT_SIZE = 8192


def is_installed() -> bool:
    try:
        importlib.metadata.version("vllm")
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def is_running() -> bool:
    for process in psutil.process_iter():
        try:
            if process.name() == "vllm":
                return True
        except psutil.NoSuchProcess:
            pass
    return False


def start(node_info: NodeInfo, model_name: str, debug: bool = False) -> bool:
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
            "11434",
            "--disable-frontend-multiprocessing",
        ]
        if node_info.vram <= 8192:
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
        with open("vllm.log", "a") as log_file:
            process = subprocess.Popen(
                command, stdout=log_file, stderr=log_file, preexec_fn=os.setpgrp
            )
            if debug:
                print(
                    f'Started vllm process with PID: {process.pid}, logging to "vllm.log"'
                )
            return True
        if debug:
            print(f"Started vllm process with PID: {process.pid}")
        return True
    except Exception as e:
        if debug:
            print(f"Error starting vllm process: {e}")
        return False


if __name__ == "__main__":
    print(is_running())

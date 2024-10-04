from galadriel_node import config
from galadriel_node.sdk.system.gpu import has_low_memory_gpu


def execute(environment: str):
    try:
        low_mem_gpu = has_low_memory_gpu()
    except Exception as exc:
        low_mem_gpu = False
        print(f"WARNING: failed to get GPU info")
    _config = config.Config(
        is_load_env=False, environment=environment, low_gpu_mem=low_mem_gpu
    )
    config_dict = _config.as_dict()
    print("Press enter to use default values.")
    print("Or insert custom value when asked.")
    for key, value in config_dict.items():
        answer = input(f"{key} (Default: {value}): ")
        if answer:
            config_dict[key] = answer
    _config.save(config_dict=config_dict)

    print("\nGaladriel successfully initialised")
    print(f"To change values edit: {config.CONFIG_FILE_PATH}")

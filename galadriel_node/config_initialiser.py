from galadriel_node import config


def execute(environment: str):
    _config = config.Config(is_load_env=False, environment=environment)
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

import os
from typing import Any
from typing import Dict
from typing import Optional

from dotenv import load_dotenv

CONFIG_FILE_PATH = os.path.expanduser("~/.galadrielenv")

DEFAULT_ENVIRONMENT = "production"
DEFAULT_PRODUCTION_VALUES = {
    "GALADRIEL_API_URL": "https://api.galadriel.com/v1",
    "GALADRIEL_RPC_URL": "wss://api.galadriel.com/v1/node",
    "GALADRIEL_LLM_BASE_URL": "http://localhost:11434",
}

DEFAULT_LOCAL_VALUES = {
    "GALADRIEL_API_URL": "http://localhost:5000/v1",
    "GALADRIEL_RPC_URL": "ws://localhost:5000/v1/node",
    "GALADRIEL_LLM_BASE_URL": "http://10.132.0.33:11434",
}


class Config:
    def __init__(
        self, is_load_env: bool = False, environment: str = DEFAULT_ENVIRONMENT
    ):
        if is_load_env:
            load_dotenv(dotenv_path=CONFIG_FILE_PATH)

        self.GALADRIEL_ENVIRONMENT = os.getenv("GALADRIEL_ENVIRONMENT", environment)

        # Network settings
        default_values = DEFAULT_PRODUCTION_VALUES
        if self.GALADRIEL_ENVIRONMENT != "production":
            default_values = DEFAULT_LOCAL_VALUES
        self.GALADRIEL_API_URL = os.getenv(
            "GALADRIEL_API_URL", default_values["GALADRIEL_API_URL"]
        )
        self.GALADRIEL_RPC_URL = os.getenv(
            "GALADRIEL_RPC_URL", default_values["GALADRIEL_RPC_URL"]
        )
        self.GALADRIEL_API_KEY = os.getenv("GALADRIEL_API_KEY", None)

        # Other settings
        self.GALADRIEL_MODEL_ID = os.getenv(
            "GALADRIEL_MODEL_ID",
            "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
        )
        self.GALADRIEL_LLM_BASE_URL = os.getenv(
            "GALADRIEL_LLM_BASE_URL", default_values["GALADRIEL_LLM_BASE_URL"]
        )
        self.GALADRIEL_MODEL_COMMIT_HASH = "3aed33c3d2bfa212a137f6c855d79b5426862b24"
        self.MINIMUM_COMPLETIONS_TOKENS_PER_SECOND = 264

    def save(self, config_dict: Optional[Dict] = None):
        with open(CONFIG_FILE_PATH, "w") as file:
            _config = self.as_dict()
            if config_dict:
                _config = config_dict

            for key, value in _config.items():
                file.write(f'{key} = "{value}"\n')

    def as_dict(self) -> Dict[str, Any]:
        """
        Return the configuration as a dictionary.
        """
        return {
            "GALADRIEL_ENVIRONMENT": self.GALADRIEL_ENVIRONMENT,
            "GALADRIEL_API_URL": self.GALADRIEL_API_URL,
            "GALADRIEL_RPC_URL": self.GALADRIEL_RPC_URL,
            "GALADRIEL_API_KEY": self.GALADRIEL_API_KEY,
            "GALADRIEL_MODEL_ID": self.GALADRIEL_MODEL_ID,
            "GALADRIEL_LLM_BASE_URL": self.GALADRIEL_LLM_BASE_URL,
            "GALADRIEL_MODEL_COMMIT_HASH": self.GALADRIEL_MODEL_COMMIT_HASH,
        }

    def __str__(self) -> str:
        """
        Return a string representation of the configuration.
        """
        return str(self.as_dict())


# Create a global instance of the Config class
config = Config()

import os
from typing import Any
from typing import Dict
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv

from galadriel_node.sdk.entities import SdkError

CONFIG_FILE_PATH = os.path.expanduser("~/.galadrielenv")

DEFAULT_ENVIRONMENT = "production"

PRODUCTION_DOMAIN = "api.galadriel.com"
DEFAULT_PRODUCTION_VALUES = {
    "GALADRIEL_API_URL": f"https://{PRODUCTION_DOMAIN}/v1",
    "GALADRIEL_RPC_URL": f"wss://{PRODUCTION_DOMAIN}/v1/node",
    "GALADRIEL_MODEL_ID": "neuralmagic/Meta-Llama-3.1-8B-Instruct-FP8",
}

DEFAULT_LOCAL_VALUES = {
    "GALADRIEL_API_URL": "http://localhost:5000/v1",
    "GALADRIEL_RPC_URL": "ws://localhost:5000/v1/node",
    "GALADRIEL_LLM_BASE_URL": "http://10.132.0.33:11434",
    "GALADRIEL_MODEL_ID": "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
}


def valid_production_url(url, expected_scheme):
    if PRODUCTION_DOMAIN in url:
        parsed_url = urlparse(url)
        return parsed_url.scheme == expected_scheme
    return True


class Config:
    # pylint: disable=C0103
    def __init__(
        self, is_load_env: bool = True, environment: str = DEFAULT_ENVIRONMENT
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
        self.GALADRIEL_NODE_ID = os.getenv("GALADRIEL_NODE_ID", None)
        self.GALADRIEL_RPC_URL = os.getenv(
            "GALADRIEL_RPC_URL", default_values["GALADRIEL_RPC_URL"]
        )
        self.GALADRIEL_API_KEY = os.getenv("GALADRIEL_API_KEY", None)

        # Other settings
        self.GALADRIEL_MODEL_ID = os.getenv(
            "GALADRIEL_MODEL_ID",
            default_values["GALADRIEL_MODEL_ID"],
        )
        self.GALADRIEL_LLM_BASE_URL = os.getenv(
            "GALADRIEL_LLM_BASE_URL", default_values.get("GALADRIEL_LLM_BASE_URL")
        )
        self.GALADRIEL_MODEL_COMMIT_HASH = "3aed33c3d2bfa212a137f6c855d79b5426862b24"
        self.MINIMUM_COMPLETIONS_TOKENS_PER_SECOND = 264

    def save(self, config_dict: Optional[Dict] = None):
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as file:
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
            "GALADRIEL_NODE_ID": self.GALADRIEL_NODE_ID,
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

    @staticmethod
    def is_dotenv_present():
        return os.path.isfile(CONFIG_FILE_PATH)

    @staticmethod
    def validate():
        if not config.is_dotenv_present():
            raise SdkError(
                "Galadriel not initialised. Please call `galadriel init` first"
            )

        if not valid_production_url(config.GALADRIEL_API_URL, "https"):
            raise SdkError(f"Expected {config.GALADRIEL_API_URL} to use HTTPS scheme")
        if not valid_production_url(config.GALADRIEL_RPC_URL, "wss"):
            raise SdkError(f"Expected {config.GALADRIEL_RPC_URL} to use WSS scheme")


# Create a global instance of the Config class
config = Config()

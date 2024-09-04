import os
from pathlib import Path
from typing import Any
from typing import Dict

from dotenv import load_dotenv


class Config:
    def __init__(self):
        env_path = Path(".") / ".env"
        load_dotenv(dotenv_path=env_path)

        self.GALADRIEL_ENVIRONMENT = os.getenv("GALADRIEL_ENVIRONMENT", "production")

        # Network settings
        self.GALADRIEL_API_URL = os.getenv(
            "GALADRIEL_API_URL", "http://localhost:5000/v1"
        )
        self.GALADRIEL_RPC_URL = os.getenv(
            "GALADRIEL_RPC_URL", "ws://localhost:5000/v1/node"
        )
        self.GALADRIEL_API_KEY = os.getenv("GALADRIEL_API_KEY", None)

        # Other settings
        self.GALADRIEL_MODEL_ID = os.getenv(
            "GALADRIEL_MODEL_ID", "neuralmagic/Meta-Llama-3.1-8B-Instruct-FP8"
        )
        self.GALADRIEL_LLM_BASE_URL = os.getenv(
            "GALADRIEL_LLM_BASE_URL", "http://10.132.0.33:11434"
        )
        self.GALADRIEL_MODEL_COMMIT_HASH = "3aed33c3d2bfa212a137f6c855d79b5426862b24"

        self.MINIMUM_COMPLETIONS_TOKENS_PER_SECOND = 264

    def as_dict(self) -> Dict[str, Any]:
        """
        Return the configuration as a dictionary.
        """
        return {
            "GALADRIEL_ENVIRONMENT": self.GALADRIEL_ENVIRONMENT,
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

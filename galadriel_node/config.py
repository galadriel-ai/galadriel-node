import os
from typing import Dict, Any


class Config:
    def __init__(self):
        # Network settings
        self.GALADRIEL_RPC_URL = os.getenv(
            "GALADRIEL_RPC_URL", "ws://localhost:5000/v1/node"
        )
        self.GALADRIEL_API_KEY = os.getenv("GALADRIEL_API_KEY", None)

        # Other settings
        self.GALADRIEL_MODEL_ID = "llama3"
        self.GALADRIEL_LLM_BASE_URL = "http://localhost:11434"
        self.GALADRIEL_MODEL_COMMIT_HASH = "db1f81ad4b8c7e39777509fac66c652eb0a52f91"

    def as_dict(self) -> Dict[str, Any]:
        """
        Return the configuration as a dictionary.
        """
        return {
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

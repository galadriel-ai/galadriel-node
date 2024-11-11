from enum import Enum


class SdkError(Exception):
    pass


class AuthenticationError(SdkError):
    pass


class LLMEngine(Enum):
    VLLM = "vllm"
    LMDEPLOY = "lmdeploy"

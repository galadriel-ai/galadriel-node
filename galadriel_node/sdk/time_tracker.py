import time
from typing import Optional

from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionChunk


class TimeTracker:

    def __init__(self):
        # All times marked as time.time()
        self.start_time: float = 0.0
        self.first_token_time: float = 0.0
        self.next_token_time: float = 0.0
        self.usage: Optional[CompletionUsage] = None

    def start(self):
        self.start_time = time.time()

    def chunk_received(self, chunk: Optional[ChatCompletionChunk]):
        if _is_chunk_with_tokens(chunk):
            if self.first_token_time:
                self.next_token_time = time.time()
            else:
                self.first_token_time = time.time()

        if chunk and chunk.usage:
            self.usage = chunk.usage

    def get_time_to_first_token(self) -> float:
        """
        Returns TTFT
        """
        if self.first_token_time:
            return self.first_token_time - self.start_time
        return 0.0

    def get_total_time(self) -> float:
        if self.next_token_time:
            return self.next_token_time - self.start_time
        if self.first_token_time:
            return self.first_token_time - self.start_time
        return 0.0

    def get_throughput(self) -> float:
        """
        Returns tokens per second since the first token was generated
        """
        if self.usage and self.next_token_time:
            duration = self.next_token_time - self.first_token_time
            if duration:
                return self.usage.completion_tokens / duration

        # If token has been received we should still return something
        if self.first_token_time:
            return 1.0
        return 0.0

    def get_prompt_tokens(self) -> int:
        if self.usage:
            return self.usage.prompt_tokens
        return 0


def _is_chunk_with_tokens(chunk: Optional[ChatCompletionChunk]):
    return (
        chunk
        and chunk.choices
        and chunk.choices[0].delta
        and (
            chunk.choices[0].delta.content
            or chunk.choices[0].delta.function_call
            or chunk.choices[0].delta.tool_calls
        )
    )

from http import HTTPStatus

import openai

from galadriel_node.sdk.logging_utils import get_node_logger
from galadriel_node.sdk.node.checks import llm_http_check
from galadriel_node.sdk.node.checks import llm_sanity_check

logger = get_node_logger()


async def execute(llm_base_url: str, model_id: str) -> bool:
    try:
        response = await llm_http_check.execute(llm_base_url)
        if response.ok:
            logger.info(
                f"[bold green]\N{CHECK MARK} LLM server at {llm_base_url} is accessible via HTTP.[/bold green]"
            )
        else:
            logger.info(
                f"[bold red]\N{CROSS MARK} LLM server at {llm_base_url} "
                f"returned status code: {response.status}[/bold red]"
            )
            return False
    except Exception as e:
        logger.error(
            f"[bold red]\N{CROSS MARK} Failed to reach LLM server at {llm_base_url}: \n{e}[/bold red]",
            e,
        )
        return False

    try:
        response = await llm_sanity_check.execute(llm_base_url, model_id)
        if response.status_code == HTTPStatus.OK:
            logger.info(
                f"[bold green]\N{CHECK MARK} LLM server at {llm_base_url} successfully generated tokens.[/bold green]"
            )
            return True
    except openai.APIStatusError as e:
        logger.info(
            f"[bold red]\N{CROSS MARK} LLM server at {llm_base_url} "
            f"failed to generate tokens. APIStatusError: \n{e}[/bold red]"
        )
        return False
    except Exception as e:
        logger.error(
            f"[bold red]\N{CROSS MARK} LLM server at {llm_base_url} "
            f"failed to generate tokens. Exception occurred: {e}[/bold red]"
        )
        return False
    return False

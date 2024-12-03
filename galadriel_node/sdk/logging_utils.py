import logging
from logging import DEBUG, INFO

from rich.logging import RichHandler

GALADRIEL_NODE_LOGGER = "galadriel_node"


def init_logging(debug: bool):
    log_level = DEBUG if debug else INFO
    rich_handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        show_level=True,
        show_path=True,
        markup=True,
    )
    logger = logging.getLogger(GALADRIEL_NODE_LOGGER)
    logger.setLevel(log_level)
    formatter = logging.Formatter("%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    rich_handler.setFormatter(formatter)
    logger.addHandler(rich_handler)
    logger.propagate = False


def get_node_logger():
    return logging.getLogger(GALADRIEL_NODE_LOGGER)

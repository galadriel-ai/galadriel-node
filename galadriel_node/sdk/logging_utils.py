from logging import DEBUG, INFO, basicConfig

from rich.logging import RichHandler


def init_logging(debug: bool):
    log_level = DEBUG if debug else INFO
    rich_handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        show_level=True,
        show_path=True,
        markup=True,
    )

    basicConfig(
        format="%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=log_level,
        handlers=[rich_handler],
    )

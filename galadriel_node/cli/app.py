import importlib.metadata

import typer

from galadriel_node.cli.network import network_app
from galadriel_node.cli.node import node_app
from galadriel_node import config
from galadriel_node import config_initialiser

app = typer.Typer(
    no_args_is_help=True,
)

app.add_typer(node_app)
app.add_typer(network_app)


@app.command("init", help="Galadriel tool to initialise the node configurations")
def init(
    environment: str = typer.Option(config.DEFAULT_ENVIRONMENT, help="Environment"),
):
    config_initialiser.execute(environment)


@app.callback(invoke_without_command=True)
def version(
    v: bool = typer.Option(None, "--version", "-v", help="Show Galadriel version.")
):
    if v:
        try:
            app_version = importlib.metadata.version("galadriel-node")
            print(f"Galadriel {app_version}", flush=True)
        except Exception as exc:
            print("Failed to get version:", exc)


if __name__ == "__main__":
    app()

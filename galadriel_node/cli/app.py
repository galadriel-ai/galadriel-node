import typer

from galadriel_node.cli.node import node_app

app = typer.Typer(
    no_args_is_help=True,
)

app.add_typer(node_app)

if __name__ == "__main__":
    app()

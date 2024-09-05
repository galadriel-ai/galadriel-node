from galadriel_node.config import config


def test_config():
    assert config.GALADRIEL_RPC_URL == "wss://api.galadriel.com/v1/node"

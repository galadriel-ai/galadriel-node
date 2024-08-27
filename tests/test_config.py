from galadriel_node.config import config

def test_config():
    assert config.GALADRIEL_RPC_URL == "ws://localhost:5000/v1/nodeX"
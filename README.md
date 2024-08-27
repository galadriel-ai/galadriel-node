# Galadriel inference node

### Installation

```shell
pip install -e .
```

### Running with LLM

Setup ollama:

```shell
# Install ollama on unix natively:
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3

# Or docker:
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3
```

Run the node:

```shell
galadriel node run
```


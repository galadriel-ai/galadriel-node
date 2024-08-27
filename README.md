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


## Production VM deployment

Make sure GPU exists etc
```
nvidia-smi
```

Run vLLM
```
python3 -m venv venv
source venv/bin/activate
pip install vllm
pip install jinja2

mkdir logs

HUGGING_FACE_HUB_TOKEN=<HUGGING_FACE_TOKEN> \
nohup vllm serve hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4 \
    --revision db1f81ad4b8c7e39777509fac66c652eb0a52f91 \
    --max-model-len 16384 \
    --gpu-memory-utilization 1 \
    --host localhost \
    --disable-frontend-multiprocessing \
    --port 11434 > logs/logs0.log 2>&1 &
```

Setup node
```
ssh-keygen -t rsa -b 4096
# Add public key to repo "deploy keys"
# clone repo
cd galadriel-node
pip install -e .
```

Run node
```
GALADRIEL_API_KEY=<API KEY> \
    GALADRIEL_RPC_URL=ws://34.78.190.171/v1/node \
    nohup galadriel node run > logs.log 2>&1 &
```
# Galadriel inference node

Run a Galadriel GPU node to provide LLM inference to the network.

Check out the [documentation](https://galadriel.mintlify.app/).

## Requirements

### Hardware requirements

- At least 4 CPU cores
- At least 8GB RAM
- A supported Nvidia GPU

### Software requirements
- linux (Ubuntu recommended)
- python (version 3.8+)
- nvidia drivers, version > 450. nvidia-smi must work

### API keys
- A valid galadriel API key


### LLM deployment

To run a Galadriel node, you must first run an LLM.

**Make sure GPU exists and nvidia drivers are installed**
```shell
nvidia-smi
```

**Run ollama natively**

```shell
curl -fsSL https://ollama.com/install.sh | sh

systemctl status ollama
# If already running, skip this command
nohup ollama serve > logs_llm.log 2>&1 &

ollama pull llama3.1:8b-instruct-q8_0
```

**Or run ollama in docker**
```shell
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.1:8b-instruct-q8_0
```

**Run ollama**  
This runs ollama on "http://localhost:11434"  
To see that it works, try calling it
```shell
curl http://0.0.0.0:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: asd" \
  -d '{
    "model": "llama3.1:8b-instruct-q8_0",
    "messages": [
        {
        "role": "system",
        "content": "You are a helpful assistant."
        },
        {
        "role": "user",
        "content": "Whats up?"
        }
    ]
}'
```

## Run a Galadriel-node

**Install requirements**
```shell
pip install galadriel-node
```

**Setup the environment**  
Only update values that are not the default ones, and make sure to set the API key
```
galadriel init
```

**Run the node**
```shell
galadriel node run
# Or in the background
nohup galadriel node run > logs.log 2>&1 &
```

**Environment values can be overwritten in the run command**
```shell
GALADRIEL_LLM_BASE_URL="http://localhost:8000" galadriel node run
# or with nohup
GALADRIEL_LLM_BASE_URL="http://localhost:8000" nohup galadriel node run > logs.log 2>&1 &
```

**Check the node status and metrics**
```shell
galadriel node status

galadriel node stats
```
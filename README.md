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
- nvidia drivers, version > 450. `nvidia-smi` must work

### API keys
- A valid galadriel API key
- A valid [huggingface](https://huggingface.co/) access token


### LLM deployment

To run a Galadriel node, you must first run an LLM.

**Create a python environment**
```shell
python3 -m venv venv
source venv/bin/activate
```

**Install vllm**
```shell
pip install vllm==0.5.5
```

**Run vllm**
```shell
HUGGING_FACE_HUB_TOKEN=<HUGGING_FACE_TOKEN> \
  nohup vllm serve neuralmagic/Meta-Llama-3.1-8B-Instruct-FP8 \
  --revision 3aed33c3d2bfa212a137f6c855d79b5426862b24 \
  --max-model-len 8192 \
  --gpu-memory-utilization 1 \
  --host 127.0.0.1 \
  --disable-frontend-multiprocessing \
  --port 11434 > logs_llm.log 2>&1 &
```

**Ensure vllm works**
```shell
tail -f logs_llm.log
```
Should see something like `INFO: Uvicorn running on http://127.0.0.1:11434`

Once you see the API is working try calling it
```shell
curl http://localhost:11434/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: a" \
-d '{
    "model": "neuralmagic/Meta-Llama-3.1-8B-Instruct-FP8",
    "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hi, whats up?"
    }
  ]
}'
```

### Run a GPU node from the command line

**Create a (separate) python environment**
```shell
deactivate
mkdir galadriel
cd galadriel
python3 -m venv venv
source venv/bin/activate
```

**Install galadriel-node**
```shell
pip install galadriel-node
```

**Setup the environment**

Only update values that are not the default ones, and make sure to set the API key
```shell
galadriel init
```

**Run the node**
```shell
galadriel node run
```
If this is your first time running the GPU node, it will perform hardware validation and LLM benchmarking, to ensure your setup is working correctly and is fast enough.

**Or run with nohup to run in the background**
```shell
nohup galadriel node run > logs.log 2>&1 &
```

**Or include .env values in the command**
```shell
GALADRIEL_LLM_BASE_URL="http://localhost:8000" galadriel node run
# or with nohup
GALADRIEL_LLM_BASE_URL="http://localhost:8000" nohup galadriel node run > logs.log 2>&1 &
```

**Check node status**
```shell
galadriel node status
```
Should see status: online

**Check node metrics**
```shell
galadriel node stats
```

### Development

* Code formatting: 

`black .`
 
* Linting: 
 
`pylint --rcfile=setup.cfg galadriel_node/*`

* MyPy: 
 
`mypy .`

* Unit testing:

`python -m pytest tests`

# Galadriel inference node

### Installation

```shell
# Setup venv or whatever environment you wish
python3 -m venv venv
source venv/bin/activate

pip install -e .
```

**Setup .env**
```
cp template.env .env
# Update values according to your setup
```

**Run the node**
```shell
galadriel node run
```

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


## LLM deployment

**Make sure GPU exists and nvidia drivers are installed**
```shell
nvidia-smi
```

**Run vLLM natively**

Make sure you create a separate python env
```shell
python3 -m venv venv
source venv/bin/activate
pip install vllm
```

**Run vllm**

This runs vllm on "http://localhost:11434", that is the default value 
```shell
HUGGING_FACE_HUB_TOKEN=<HUGGING_FACE_TOKEN> \
nohup vllm serve neuralmagic/Meta-Llama-3.1-8B-Instruct-FP8 \
    --revision 3aed33c3d2bfa212a137f6c855d79b5426862b24 \
    --max-model-len 16384 \
    --gpu-memory-utilization 1 \
    --host localhost \
    --disable-frontend-multiprocessing \
    --port 11434 > logs_llm.log 2>&1 &
```


### TODO: remove this part, once node released
### Development
**Setup node**
```
ssh-keygen -t rsa -b 4096
# Add public key to repo "deploy keys"
# clone repo
cd galadriel-node

# deactivate other venv 
# deactivate
python3 -m venv venv
source venv/bin/activate

pip install -e .
```

Run node
```
GALADRIEL_API_KEY=<API KEY> \
    GALADRIEL_RPC_URL=ws://34.78.190.171/v1/node \
    nohup galadriel node run > logs.log 2>&1 &
```
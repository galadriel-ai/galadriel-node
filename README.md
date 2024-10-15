# Galadriel inference node

Run a Galadriel GPU node to provide LLM inference to the network.

Check out the [documentation](https://docs.galadriel.com/nodes).


## Requirements

### Hardware requirements

- At least 4 CPU cores
- At least 8GB RAM
- A supported Nvidia GPU

### Software requirements
- linux (Ubuntu recommended)
- python (version 3.10+)
- nvidia drivers, version > 450. `nvidia-smi` must work

### API keys
- A valid galadriel API key
- A valid [huggingface](https://huggingface.co/) access token

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

**Check LLM status**
```shell
galadriel node llm-status
```
Should see status like:
```
✓ LLM server at http://your_llm_address is accessible via HTTP.
✓ LLM server at http://your_llm_address successfully generated tokens.
```

**Check node metrics**
```shell
galadriel node stats
```

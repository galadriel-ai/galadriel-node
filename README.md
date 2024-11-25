# Galadriel inference node

Galadriel is building the world’s largest distributed LLM inference network - for developers to scale their LLM apps while cutting costs.

Run a Galadriel GPU node to provide LLM inference to the network.

Check out the quickstart in the [documentation](https://docs.galadriel.com/nodes/quickstart) to get started.


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
- A valid galadriel API key, gotten from the Galadriel [dashboard](https://dashboard.galadriel.com/)

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
If this is your first time running the GPU node, it will perform hardware validation and LLM benchmarking, 
to ensure your setup is working correctly and is fast enough.

**Or run with nohup to run in the background**
```shell
nohup galadriel node run > logs.log 2>&1 &
```

**Check node status**
```shell
galadriel node status
```
Should see status: online


### Additional commands

**Check LLM status**
```shell
galadriel node llm-status
```
Should see something like this:
```
✓ LLM server at http://your_llm_address is accessible via HTTP.
✓ LLM server at http://your_llm_address successfully generated tokens.
```

**Check node stats**
```shell
galadriel node stats
```

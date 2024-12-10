# Development setup 

### Requirement

- Python >=3.8
- Git 

### Setup locally

#### Clone the project 
```shell
git clone git@github.com:galadriel-ai/galadriel-node.git
cd galadriel-node
```

#### Create virtualenv and install dependencies
```shell
deactivate
python3 -m venv venv
source venv/bin/activate
pip install -e '.[dev]'
pre-commit install
```

#### Setup local env variables
Run the following command to go through a setup wizard for your local galadriel node:
```shell
python galadriel_node/cli/app.py init --environment local
```
Make sure to set the `GALADRIEL_LLM_BASE_URL` to the remote GPU worker, instead of your localhost.

> **_NOTE:_**  The initializing setup wizard may not be super up-to-date sometimes, so make sure to check if any environmental variables are missing in the [config.py](galadriel_node/config.py).

> **_NOTE:_** Since vLLM only supports Linux machines with a GPU, you can point the node to a vLLM setup by setting the `GALADRIEL_LLM_BASE_URL` in your `~/galadrielenv` file.

#### Verify the LLM status
Run the following command to check if the `GALADRIEL_LLM_BASE_URL` is correctly set and running normally
```shell
python galadriel_node/cli/app.py node llm-status
```
Should see status like:
```
✓ LLM server at http://your_llm_address is accessible via HTTP.
✓ LLM server at http://your_llm_address successfully generated tokens.
```

#### Run the node
Run the node locally:
```shell
python galadriel_node/cli/app.py node run
```

### Formatting and linting
Install pre-commit hooks by running `pre-commit install` or run the following command to format the code:

* Code formatting:

`black .`
 
* Linting: 
 
`pylint --rcfile=setup.cfg galadriel_node/*`

* MyPy: 
 
`mypy .`

* Unit testing:

`python -m pytest tests`

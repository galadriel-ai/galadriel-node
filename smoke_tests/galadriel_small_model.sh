#!/bin/bash

# display the content of the file
cat ${ENV_FILE}

# run the model
# Get the node stats
source venv/bin/activate
nvidia-smi
(galadriel node run 2>&1)  > node_run.output

# check if the node is indeed running
tail -f node_run.output


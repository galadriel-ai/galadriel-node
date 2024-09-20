#!/bin/bash

ENV_FILE="$HOME/.galadrielenv"
SMALL_MODEL="microsoft/phi-2"

# change the model name in .galadrielenv
sed - i '' "s/^GALADRIEL_MODEL_ID =.*/GALADRIEL_MODEL_ID = ${SMALL_MODEL}/" "${ENV_FILE}"

# display the content of the file
cat ${ENV_FILE}

# run the model
# Get the node stats
source venv/bin/activate
(galadriel node run 2>&1)  > node_run.output

# check if the node is indeed running
tail -f node_run.output


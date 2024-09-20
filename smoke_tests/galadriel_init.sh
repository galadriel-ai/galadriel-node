#!/bin/bash

ENV_FILE="$HOME/.galadrielenv"
rm -f ${ENV_FILE}

GALADRIEL_ENVIRONMENT="production"
GALADRIEL_API_URL="https://api.galadriel.com/v1"
GALADRIEL_NODE_ID="mom_chest_cube_canyon_super"
GALADRIEL_RPC_URL="wss://api.galadriel.com/v1/node"
GALADRIEL_API_KEY="gal-Vv_IGy_6JHFOKktF5frIAuEMjV7H382ZsfZN78hJ6NcZQqvN"
GALADRIEL_MODEL_ID="microsoft/phi-1_5"
{
  echo "GALADRIEL_ENVIRONMENT=${GALADRIEL_ENVIRONMENT}"
  echo "GALADRIEL_API_URL=${GALADRIEL_API_URL}"
  echo "GALADRIEL_NODE_ID=${GALADRIEL_NODE_ID}"
  echo "GALADRIEL_RPC_URL=${GALADRIEL_RPC_URL}"
  echo "GALADRIEL_API_KEY=${GALADRIEL_API_KEY}"
  echo "GALADRIEL_MODEL_ID=${GALADRIEL_MODEL_ID}"
} > ${ENV_FILE}

# display the content of the file
# will be useful for debugging
cat ${ENV_FILE}
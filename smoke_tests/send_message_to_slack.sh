#!/bin/zsh

# The message to be sent to Slack

MESSAGE=$1
SLACK_WEBHOOK_URL=$2
# Sending the message to Slack
payload="{
    \"text\": \"${MESSAGE}\"
}"

curl -X POST -H 'Content-type: application/json' --data "$payload" "${SLACK_WEBHOOK_URL}"

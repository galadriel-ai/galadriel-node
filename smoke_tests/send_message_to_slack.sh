#!/bin/zsh

# The message to be sent to Slack
KEY=$1
VALUE=$1
SLACK_WEBHOOK_URL=$3
# Sending the message to Slack
payload="{
    \"${KEY}\": \"${VALUE}\"
}"

curl -X POST -H 'Content-type: application/json' --data "$payload" $SLACK_WEBHOOK_URL
#!/usr/bin/env bash

# get the node status
galadriel node status 2>&1  node_status.output

# check if the output is empty
if [ ! -s node_status.output ]; then
    ./smoke_test/send_message_to_slack.sh "node_status" "ERROR: produced no output" "$SLACK_WEBHOOK_URL"
    exit
fi

if grep -i "error" node_status.output; then
    ./smoke_test/send_message_to_slack.sh "node_status" "ERROR: Failed to run 'galadriel node status'" "$SLACK_WEBHOOK_URL"
fi

if grep -i "status: offline" node_status.output; then
    ./smoke_test/send_message_to_slack.sh "node_status" "ERROR: Node is offline" "$SLACK_WEBHOOK_URL"
fi

if grep -q "status: online" node_status.output; then
    echo "Node status is OK". # No need to send message in slack if everything is okay
fi
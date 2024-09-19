#!/bin/bash

# Get the node status
source venv/bin/activate
(galadriel node status 2>&1) >  node_status.output
cat node_status.output

# Check if the output is empty
if [ ! -s node_status.output ]; then
    ./smoke_tests/send_message_to_slack.sh "galadriel node status: Produced no output" "$SLACK_WEBHOOK_URL"
    exit 1
fi

# Encountered some error
if grep -i "error" node_status.output; then
    ./smoke_tests/send_message_to_slack.sh "galadriel node status: Failed to run" "$SLACK_WEBHOOK_URL"
    exit 1
fi

# Check if the status return the node id of the smoke test user
if grep -q "node_id: 066ebbf8-9ec7-7618-8000-3fb130706ad9" node_status.output; then
    echo "Node status is OK". # No need to send message in slack if everything is okay
    exit 0
fi

# Unknown error
./smoke_tests/send_message_to_slack.sh "galadriel node status: Unknown error" "$SLACK_WEBHOOK_URL"
exit 1

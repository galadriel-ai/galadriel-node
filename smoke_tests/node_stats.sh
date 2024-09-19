#!/usr/bin/env bash

# get the node stats
galadriel node stats 2>&1  node_stats.output

# check if the output is empty
if [ ! -s node_stats.output ]; then
    ./smoke_test/send_message_to_slack.sh "node_stats" "ERROR: produced no output" "$SLACK_WEBHOOK_URL"
    exit
fi

if grep -i "error" node_stats.output; then
    ./smoke_test/send_message_to_slack.sh "node_stats" "ERROR: Failed to run 'galadriel node stats'" "$SLACK_WEBHOOK_URL"
fi

if grep -q "requests_served" node_stats.output; then
    echo "Node stats is OK". # No need to send message in slack if everything is okay
fi


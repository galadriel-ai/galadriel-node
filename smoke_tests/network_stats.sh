#!/bin/bash

# Get the network stats
source venv/bin/activate
(galadriel network stats 2>&1)  > network_stats.output
cat network_stats.output

# Check if the output is empty
if [ ! -s network_stats.output ]; then
    ./smoke_tests/send_message_to_slack.sh "galadriel network stats: Produced no output" "$SLACK_WEBHOOK_URL"
    exit 1
fi

# Encountered some error
if grep -i "error" network_stats.output; then
    ./smoke_tests/send_message_to_slack.sh "galadriel network stats: Failed to run " "$SLACK_WEBHOOK_URL"
    exit 1
fi

# got the stats
if grep -q "nodes_count" network_stats.output; then
    echo "galadriel network stats: Node stats is OK" # No need to send message in slack if everything is okay
    exit 0
fi

# Unknown error
./smoke_tests/send_message_to_slack.sh "galadriel network stats: ERROR: Unknown error" "$SLACK_WEBHOOK_URL"
exit 1
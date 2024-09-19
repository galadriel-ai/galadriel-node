#!/bin/zsh

# Get the node stats
(galadriel node stats 2>&1)  > node_stats.output

# Check if the output is empty
if [ ! -s node_stats.output ]; then
    ./smoke_tests/send_message_to_slack.sh "galadriel node stats: Produced no output" "$SLACK_WEBHOOK_URL"
    exit 1
fi

# Encountered some error
if grep -i "error" node_stats.output; then
    ./smoke_tests/send_message_to_slack.sh "galadriel node stats: Failed to run " "$SLACK_WEBHOOK_URL"
    exit 1
fi

# got the stats
if grep -q "requests_served" node_stats.output; then
    echo "galadriel node stats: Node stats is OK" # No need to send message in slack if everything is okay
    exit 0
fi

# Unknown error
./smoke_tests/send_message_to_slack.sh "galadriel node stats: ERROR: Unknown error" "$SLACK_WEBHOOK_URL"
exit 1
#!/bin/bash

TIMEOUT=20  # Timeout in seconds
INTERVAL=1  # Interval for checking log file

# display the content of the file
cat ${ENV_FILE}

LOGFILE="run_output.txt"
# Get the node stats
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    exit 1
fi

nvidia-smi
ls galadriel_node/cli/node.py
if [ ! -f galadriel_node/cli/node.py ]; then
    echo "File galadriel_node/cli/node.py does not exist"
    exit 1
fi

echo "Running command: python3 galadriel_node/cli/node.py node run > $LOGFILE 2>&1 &"
python3 galadriel_node/cli/node.py node run > $LOGFILE 2>&1 &
CMD_PID=$!

if [ -z "$CMD_PID" ]; then
    echo "Failed to start the command"
    exit 1
fi

start_time=$(date +%s)

while true; do
    # Check the log file for "Done" (Success) and "ERROR" (Failure)
    if grep -q "Done" "$LOGFILE"; then
        echo "Success: 'Done' found in the log file"
        kill $CMD_PID
        exit 0
    elif grep -q "ERROR" "$LOGFILE"; then
        echo "Failure: 'ERROR' found in the log file"
        kill $CMD_PID
        exit 1
    fi

    # Check if timeout is reached
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    if [ $elapsed_time -ge $TIMEOUT ]; then
        echo "Timeout reached, killing the command..."
        kill $CMD_PID
        cat $LOGFILE
        exit 2
    fi

    # Wait for the specified interval before checking again
    sleep $INTERVAL
done



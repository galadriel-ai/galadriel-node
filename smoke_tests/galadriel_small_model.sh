#!/bin/bash

TIMEOUT=20  # Timeout in seconds
INTERVAL=1  # Interval for checking log file

# display the content of the file
cat ${ENV_FILE}

# run the model
# Get the node stats
source venv/bin/activate
nvidia-smi
ls -alrt
python3 galadriel_node/cli/node.py node stats
python3 galadriel_node/cli/node.py node run > run_output.txt 2>&1 &
CMD_PID=$!

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
        cat run_output.txt
        exit 2
    fi

    # Wait for the specified interval before checking again
    sleep $INTERVAL
done



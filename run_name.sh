#!/bin/bash

# Default log level
LOG="info"

# List of valid log levels
VALID_LOG_LEVELS=("debug" "warning" "info" "critical")

# Check if a log level argument was provided
if [[ $# -gt 0 ]]; then
    # Validate the provided log level
    if [[ " ${VALID_LOG_LEVELS[*]} " =~ " $1 " ]]; then
        LOG=$1
    else
        echo "Invalid log level: $1. Valid options are: ${VALID_LOG_LEVELS[*]}."
        exit 1
    fi
fi

SCHEDULER_NAME=$(cd scheduler/repo && git rev-parse --abbrev-ref HEAD)
export SCHEDULER_NAME
export LOG
docker compose up
#!/bin/bash

# Test: 10 usuarios concurrentes usando Siege

RESULTS_FILE="./test_result.txt"

siege \
    --concurrent=5 \
    --reps=10 \
    --content-type="application/json" \
    --header="Accept: application/json, text/event-stream" \
    "http://localhost:8000/v1/devex-mcp POST < payload.json" \
    2>&1 | tee "$RESULTS_FILE"

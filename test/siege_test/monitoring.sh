#!/bin/bash

# Monitorea Docker - memoria y CPU

docker stats devex-mcp --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.CPUPerc}}"

#!/bin/bash
# Quick commands for EC2

# Set PYTHONPATH
export PYTHONPATH=/home/ubuntu/ztrader

# Activate venv
source ~/ztrader/venv/bin/activate

# Run the command passed as argument
cd ~/ztrader
"$@"

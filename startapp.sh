#!/bin/bash

# Set bash parameters to catch errors
set -euo pipefail

# Use pm2 manager to run todoapp
pm2 start app.py --name todo-app --log logs/app.log -- prod --interpreter python3

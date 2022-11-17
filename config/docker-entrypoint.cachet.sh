#!/bin/sh

set -e

while ! nc -z cachet 8000; do
  echo "Waiting for Cachet server to accept connections on port 8000..."
  sleep 1s
done

sleep 10s

python3 cachet_url_monitor/scheduler.py config/config.yml

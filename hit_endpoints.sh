#!/usr/bin/env bash
curl -s http://127.0.0.1:8000/healthz > /dev/null
curl -s http://127.0.0.1:8000/docs    > /dev/null
echo "Endpoints hit."
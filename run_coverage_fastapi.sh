#!/usr/bin/env bash
coverage run -m uvicorn api.main:app --host 127.0.0.1 --port 8000
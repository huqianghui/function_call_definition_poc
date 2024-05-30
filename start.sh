#!/bin/sh
gunicorn -b 0.0.0.0:8000 app:app1 --workers 4 --threads 4 --preload &
gunicorn -b 0.0.0.0:8001 app:app2 --workers 4 --threads 4 --preload &

# Wait for all background processes to finish
wait
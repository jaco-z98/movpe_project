#!/bin/bash

# Start sqlite-web in the background (only accessible locally)
sqlite_web /app/raw_measurements.sqlite3 --port 8085 --host 127.0.0.1 &
sqlite_web /app/db.sqlite3 --port 8086 --host 127.0.0.1 &

# Run Django migrations
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py migrate --database=raw_measurements

# Start Django server
python3 manage.py runserver 0.0.0.0:8234

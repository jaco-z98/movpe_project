#!/bin/bash

# Start sqlite-web in the background
sqlite_web /app/db.sqlite3 --port 8085 --host 0.0.0.0 &

python3 manage.py makemigrations

# Run Django migrations
python3 manage.py migrate

# Start Django server
python3 manage.py runserver 0.0.0.0:8234

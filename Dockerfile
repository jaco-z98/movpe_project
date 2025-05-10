FROM python:3.13.3-bookworm

WORKDIR /app

RUN apt update && apt install -y iproute2
RUN pip3 install sqlite-web
RUN pip3 install Django pandas plotly scipy
RUN pip3 install requests

# RUN sqlite_web /app/db.sqlite3 --port 8085

RUN apt install dumb-init

COPY ./ /app

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/app/start.sh"]

# CMD dumb-init python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8234

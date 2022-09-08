FROM python:slim

RUN useradd easyblogbd

WORKDIR /home/easyblogbd

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql cryptography

COPY app app
COPY migrations migrations
COPY easyblogbd.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP easyblogbd.py

RUN chown -R easyblogbd:easyblogbd ./
USER easyblogbd

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
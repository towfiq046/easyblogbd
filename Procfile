web: flask db upgrade; flask translate compile; gunicorn easyblogbd:app
worker: rq worker -u $REDIS_URL easyblogbd-tasks
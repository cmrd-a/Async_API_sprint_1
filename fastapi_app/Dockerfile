FROM python:3.10

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /opt/app

COPY requirements.txt requirements.txt
RUN  pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY src .

CMD gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
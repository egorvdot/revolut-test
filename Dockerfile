FROM python:3.6

EXPOSE 8000

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY nest.py nest.py
COPY service.py service.py

CMD python -m service

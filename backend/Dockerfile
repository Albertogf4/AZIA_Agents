FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -U langgraph==0.3.34
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5328

ENV FLASK_APP=api/app.py
ENV FLASK_ENV=development


CMD ["flask", "run", "--host=0.0.0.0", "--port=5328"]

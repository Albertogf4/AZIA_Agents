FROM python:3.12-slim

WORKDIR /app

# Copia los requirements desde la carpeta actual
COPY requirements.txt .

# Instala dependencias
RUN pip install -U langgraph==0.3.34
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Puerto
EXPOSE 5328

# Variables de entorno
ENV FLASK_APP=api/app.py
ENV FLASK_ENV=production

# Comando de arranque
CMD ["flask", "run", "--host=0.0.0.0", "--port=5328"]

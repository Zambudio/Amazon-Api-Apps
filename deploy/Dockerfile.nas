FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias necesarias
COPY requirements_server.txt .
RUN pip install --no-cache-dir -r requirements_server.txt

# Copiamos todo el proyecto para que FastApi vea la carpeta src
COPY . .

# Exponemos el puerto
EXPOSE 8000

# Iniciamos el servidor
CMD ["uvicorn", "src.server.nas_api:app", "--host", "0.0.0.0", "--port", "8000"]

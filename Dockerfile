# Usamos una imagen base oficial de Python ligera
FROM python:3.11-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema necesarias para Django y psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos solo el archivo de dependencias para aprovechar el cache de Docker
COPY requirements.txt .

# Instalamos las dependencias usando pip
# Usamos --no-cache-dir para evitar almacenar caché y reducir tamaño de la imagen
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

# Exponemos el puerto
EXPOSE 8000

# Comando para correr el servidor (en producción usar gunicorn)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
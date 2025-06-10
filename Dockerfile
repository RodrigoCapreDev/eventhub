# Usamos una imagen base oficial de Python ligera
FROM python:3.13.4-slim-bullseye

# Variables de entorno para evitar archivos .pyc y logs en buffer
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos solo el archivo de dependencias para aprovechar el cache de Docker
COPY requirements.txt .

# Instalamos dependencias del sistema necesarias para Django y psycopg2
# Instala build-essential solo para compilar, luego lo elimina
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    # Instalamos las dependencias usando pip
    # Usamos --no-cache-dir para evitar almacenar caché y reducir tamaño de la imagen
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el resto del proyecto
COPY . .

# Exponemos el puerto
EXPOSE 8000

# Comando para aplicar las migraciones y después levantar el servidor (en producción usar gunicorn)
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
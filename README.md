# Eventhub

Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP

## Integrantes
- Alvite Damián 32422
- Capre Rodrigo 31877
- Elizalde Benjamín 32030
- Canu Santiago 31626

## Dependencias

- python 3
- Django
- sqlite
- playwright
- ruff

## Instalar dependencias

`pip install -r requirements.txt`

## Iniciar la Base de Datos

`python manage.py migrate`

### Crear usuario admin

`python manage.py createsuperuser`

### Llenar la base de datos

`python manage.py loaddata fixtures/events.json`

## Iniciar app

`python manage.py runserver`

## Convenciones de ramas (Branch Naming)

Para mantener un orden claro en el repositorio, seguimos estas convenciones para nombrar las ramas, usando guion bajo `_` (**snake_case**) para separar palabras dentro del nombre, y slash `/` para separar el prefijo del nombre de la rama:

| Prefijo    | Uso principal                                            | Ejemplo                     |
|------------|---------------------------------------------------------|-----------------------------|
| `feature/` | Nuevas funcionalidades o mejoras                         | `feature/agregar_login`     |
| `fix/`     | Corrección de errores o bugs                             | `fix/arreglar_error_login`  |
| `infra/`   | Cambios en infraestructura y configuraciones técnicas   | `infra/configurar_dockerfile`|
| `refactor/`| Cambios en código para mejorar estructura o legibilidad sin agregar ni arreglar funcionalidad | `refactor/limpieza_codigo`  |
| `docs/`    | Cambios o mejoras en la documentación                    | `docs/actualizar_readme`    |

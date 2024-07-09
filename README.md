# ECG Data Migration API

Este proyecto es una API para migrar datos de señales ECG desde el servidor de PhysioNet a una base de datos MongoDB.

## Requisitos

Antes de empezar, asegúrate de tener los siguientes requisitos:

1. **Python 3.8+**: Asegúrate de tener Python instalado en tu sistema.
2. **MongoDB**: Debes tener una instancia de MongoDB corriendo en tu máquina o en un servidor accesible.
3. **FastAPI**: Este proyecto utiliza FastAPI para crear la API.

## Instalación

### Clonar el repositorio

Primero, clona este repositorio en tu máquina local:

```bash
git clone https://github.com/anders97d/ECG-analyze.git
cd ECG-analyze

python -m venv venv
source venv/bin/activate  # En Windows usa `venv\Scripts\activate`

pip install -r requirements.txt

client = MongoClient('mongodb://localhost:27017/')

uvicorn main:app --reload

GET /migrate


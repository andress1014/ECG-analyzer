from fastapi import FastAPI
import requests
import pymongo
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId

app = FastAPI()

# Conexión a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.ecg_database
collection = db.ecg_signals

# Modelo de datos
class SignalData(BaseModel):
    name: str
    units: str
    t0: int
    tf: int
    gain: int
    base: int
    tps: int
    scale: int
    samp: list

@app.get("/migrate")
def migrate_data():
    # Obtener datos desde el endpoint
    url = "https://physionet.org/lightwave/server?action=fetch&db=ludb/1.0.1&record=data/1&signal=i&signal=ii&signal=iii&signal=avr&signal=avl&signal=avf&signal=v1&signal=v2&signal=v3&signal=v4&signal=v5&signal=v6&t0=0&dt=10"
    response = requests.get(url)
    
    if response.status_code != 200:
        return {"error": "Failed to fetch data from the endpoint"}

    data = response.json().get("fetch", {}).get("signal", [])

    # Imprimir el nombre del primer elemento de la señal para depuración
    if data:
        print(f"First signal name: {data[0]['name']}")
    
    # Migrar datos a MongoDB
    migrated_count = 0
    for signal in data:
        signal_data = SignalData(**signal)
        result = collection.insert_one(signal_data.dict())
        if result.inserted_id:
            migrated_count += 1
        else:
            print(f"Failed to insert signal: {signal_data.name}")

    return {"message": f"Migrated {migrated_count} signals to MongoDB"}

@app.get("/test-mongo")
def test_mongo_connection():
    # Insertar un documento de prueba
    test_document = {"name": "test", "value": 123}
    inserted_id = collection.insert_one(test_document).inserted_id
    
    # Recuperar el documento de prueba
    retrieved_document = collection.find_one({"_id": inserted_id})
    
    # Eliminar el documento de prueba para limpieza
    collection.delete_one({"_id": inserted_id})
    
    if retrieved_document:
        # Convertir ObjectId a string
        retrieved_document['id'] = str(retrieved_document['_id'])
        del retrieved_document['_id']
        return {"message": "Connection to MongoDB is successful", "document": retrieved_document}
    else:
        return {"message": "Failed to retrieve document from MongoDB"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the ECG Data Migration API"}

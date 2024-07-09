from fastapi import FastAPI
import requests
import pymongo
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# Conexión a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.ecg_database
collection = db.ecg_signals

# Modelo de datos para la señal
class SignalData(BaseModel):
    name: str
    units: str
    t0: int
    tf: int
    gain: int
    base: int
    tps: int
    scale: int
    samp: List[int]

# Modelo de datos para el usuario y las señales
class UserData(BaseModel):
    user_info: Dict[str, str]
    signal_data: List[SignalData]

@app.get("/migrate")
def migrate_data():
    migrated_count = 0
    for record_id in range(1, 201):
        # Obtener información del usuario
        user_url = f"https://physionet.org/lightwave/server?action=info&db=ludb/1.0.1&record=data/{record_id}"
        user_response = requests.get(user_url)
        
        if user_response.status_code != 200:
            print(f"Failed to fetch user data for record {record_id}")
            continue
        
        user_info = user_response.json().get("info", {})
        
        # Procesar las notas para extraer información del usuario
        notes = user_info.get("note", [])
        user_details = {
            "age": notes[0].split(": ")[1],
            "sex": notes[1].split(": ")[1],
            "diagnoses": " ".join(notes[2:])
        }

        # Obtener datos de las señales desde el endpoint
        signal_url = f"https://physionet.org/lightwave/server?action=fetch&db=ludb/1.0.1&record=data/{record_id}&signal=i&signal=ii&signal=iii&signal=avr&signal=avl&signal=avf&signal=v1&signal=v2&signal=v3&signal=v4&signal=v5&signal=v6&t0=0&dt=5"
        signal_response = requests.get(signal_url)
        
        if signal_response.status_code != 200:
            print(f"Failed to fetch signal data for record {record_id}")
            continue

        signal_data = signal_response.json().get("fetch", {}).get("signal", [])

        # Preparar datos para MongoDB
        signal_objects = [SignalData(**signal).dict() for signal in signal_data]
        user_data = UserData(user_info=user_details, signal_data=signal_objects)
        
        # Insertar datos en MongoDB
        result = collection.insert_one(user_data.dict())
        
        if result.inserted_id:
            migrated_count += 1
        else:
            print(f"Failed to insert data for record {record_id}")

    return {"message": f"Migrated {migrated_count} records to MongoDB"}

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

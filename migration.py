import requests
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Dict

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

    return f"Migrated {migrated_count} records to MongoDB"

import requests
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Dict
import uuid
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno
record_range = 10  # Valor por defecto es 200 si no se define la variable de entorno
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mysql_database = os.getenv('MYSQL_DATABASE', 'ecg')
mysql_user = os.getenv('MYSQL_USER', 'your_username')
mysql_password = os.getenv('MYSQL_PASSWORD', 'your_password')

# Conexión a MongoDB
client = MongoClient(mongo_uri)
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
    transaction_id: str
    user_info: Dict[str, str]
    signal_data: List[SignalData]
    id_migration: str

def migrate_data():
    migrated_count = 0
    id_migration = str(uuid.uuid4())  # Generar un id_migration único para la migración actual
    for record_id in range(1, record_range + 1):
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
        user_data = UserData(transaction_id=str(uuid.uuid4()), user_info=user_details, signal_data=signal_objects, id_migration=id_migration)
        
        # Insertar datos en MongoDB
        result = collection.insert_one(user_data.dict())
        
        if result.inserted_id:
            migrated_count += 1
            # Conexión a MySQL
            try:
                connection = mysql.connector.connect(
                    host=mysql_host,
                    database=mysql_database,
                    user=mysql_user,
                    password=mysql_password
                )

                if connection.is_connected():
                    cursor = connection.cursor()

                    # Crear la tabla si no existe
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        transaction_id VARCHAR(36) NOT NULL,
                        user_age VARCHAR(10),
                        user_sex VARCHAR(10),
                        user_diagnoses TEXT,
                        commentary TEXT
                    )
                    """)

                    # Insertar los datos del usuario en MySQL
                    cursor.execute("""
                    INSERT INTO history (transaction_id, user_age, user_sex, user_diagnoses, commentary)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (user_data.transaction_id, user_details["age"], user_details["sex"], user_details["diagnoses"], ""))

                    connection.commit()
                    cursor.close()
                    connection.close()

            except Error as e:
                print(f"Error connecting to MySQL: {str(e)}")
                continue
        else:
            print(f"Failed to insert data for record {record_id}")

    return f"Migrated {migrated_count} records to MongoDB and MySQL"

# Ejecutar la migración de datos
print(migrate_data())

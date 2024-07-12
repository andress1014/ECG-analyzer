import numpy as np
import pandas as pd
from pymongo import MongoClient
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from scipy.signal import find_peaks  # Asegúrate de importar find_peaks desde scipy.signal
from fastapi import FastAPI, Request, HTTPException

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mysql_database = os.getenv('MYSQL_DATABASE', 'ecg')
mysql_user = os.getenv('MYSQL_USER', 'your_username')
mysql_password = os.getenv('MYSQL_PASSWORD', 'your_password')

def process_ecg_data(id_migration):
    try:
        # Conexión a MongoDB
        client = MongoClient(mongo_uri)
        db = client.ecg_database
        collection = db.ecg_signals

        # Obtener los datos de MongoDB filtrando por id_migration
        data = list(collection.find({"id_migration": id_migration}))

        if not data:
            raise ValueError(f"No data found for id_migration: {id_migration}")

        # Procesar los datos con Pandas
        samp_data = []

        for record in data:
            signal_data = record.get('signal_data', [])

            for signal in signal_data:
                samp = signal.get('samp', [])
                for value in samp:
                    samp_data.append({
                        'samp_value': value
                    })

        # Crear un DataFrame con los datos de las muestras
        df = pd.DataFrame(samp_data)

        # Detección de picos R
        peaks, _ = find_peaks(df['samp_value'], distance=150)  # Ajusta la distancia según tu frecuencia de muestreo
        rr_intervals = np.diff(peaks)  # Intervalos RR en muestras
        rr_intervals_time = rr_intervals / 360  # Ajusta según la frecuencia de muestreo (e.g., 360 Hz)

        # Analizar los intervalos RR
        rr_mean = np.mean(rr_intervals_time)
        rr_std = np.std(rr_intervals_time)

        # Estadísticas descriptivas de samp_value
        samp_value_description = df['samp_value'].describe().to_dict()

        # Conexión a MySQL y creación de la tabla si no existe
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
                CREATE TABLE IF NOT EXISTS statistics_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_migration VARCHAR(36) NOT NULL,
                    rr_intervals_mean DOUBLE,
                    rr_intervals_std DOUBLE,
                    samp_count DOUBLE,
                    samp_mean DOUBLE,
                    samp_std DOUBLE,
                    samp_min DOUBLE,
                    samp_25_percentile DOUBLE,
                    samp_50_percentile DOUBLE,
                    samp_75_percentile DOUBLE,
                    samp_max DOUBLE
                )
                """)

                # Insertar los datos en MySQL
                cursor.execute("""
                INSERT INTO statistics_data (
                    id_migration,
                    rr_intervals_mean,
                    rr_intervals_std,
                    samp_count,
                    samp_mean,
                    samp_std,
                    samp_min,
                    samp_25_percentile,
                    samp_50_percentile,
                    samp_75_percentile,
                    samp_max
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    id_migration,
                    rr_mean,
                    rr_std,
                    samp_value_description['count'],
                    samp_value_description['mean'],
                    samp_value_description['std'],
                    samp_value_description['min'],
                    samp_value_description['25%'],
                    samp_value_description['50%'],
                    samp_value_description['75%'],
                    samp_value_description['max']
                ))

                connection.commit()
                cursor.close()
                connection.close()

        except Error as e:
            return {"message": f"Error connecting to MySQL: {str(e)}"}

        return {
            "message": "Data processed successfully",
            "description": {
                "samp_value": samp_value_description
            },
            "rr_intervals_mean": rr_mean,
            "rr_intervals_std": rr_std
        }

    except Exception as e:
        return {"message": f"Error processing data: {str(e)}"}

# Llamada a la función
result = process_ecg_data(id_migration="your_id_migration")
print(result)

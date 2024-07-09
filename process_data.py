import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from pymongo import MongoClient

def process_ecg_data():
    try:
        # Conexión a MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client.ecg_database
        collection = db.ecg_signals

        # Obtener los datos de MongoDB
        data = list(collection.find({}))

        # Procesar los datos con Pandas
        samp_data = []

        for record in data:
            user_info = record.get('user_info', {})
            signal_data = record.get('signal_data', [])

            for signal in signal_data:
                name = signal.get('name')
                samp = signal.get('samp', [])

                for value in samp:
                    samp_data.append({
                        'user_age': user_info.get('age'),
                        'user_sex': user_info.get('sex'),
                        'user_diagnoses': user_info.get('diagnoses'),
                        'signal_name': name,
                        'samp_value': value
                    })

        # Crear un DataFrame con los datos procesados
        df = pd.DataFrame(samp_data)

        # Mostrar un resumen de los datos
        summary = df.head().to_dict(orient='records')

        # Analizar los datos (por ejemplo, estadísticas descriptivas)
        description = df.describe().to_dict()

        # Guardar el DataFrame a un archivo CSV si es necesario
        df.to_csv('ecg_data_analysis.csv', index=False)

        # Detección de picos R
        peaks, _ = find_peaks(df['samp_value'], distance=150)  # Ajusta la distancia según tu frecuencia de muestreo
        rr_intervals = np.diff(peaks)  # Intervalos RR en muestras
        rr_intervals_time = rr_intervals / 360  # Ajusta según la frecuencia de muestreo (e.g., 360 Hz)

        # Analizar los intervalos RR
        rr_mean = np.mean(rr_intervals_time)
        rr_std = np.std(rr_intervals_time)

        return {
            "message": "Data processed successfully",
            "summary": summary,
            "description": description,
            "rr_intervals_mean": rr_mean,
            "rr_intervals_std": rr_std
        }

    except Exception as e:
        return {"message": f"Error processing data: {str(e)}"}

# Llamada a la función
result = process_ecg_data()
print(result)

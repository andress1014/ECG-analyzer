# train_model.py

import os
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URI de MongoDB desde las variables de entorno
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client.ecg_database
mongo_collection = mongo_db.ecg_signals

# Consulta para obtener todos los registros de ECG que tengan datos de señales
ecg_records = mongo_collection.find({"signal_data": {"$exists": True}})

# Inicializar listas para almacenar datos de señales y etiquetas
X = []
y = []

# Iterar sobre los registros y extraer datos de señales
for record in ecg_records:
    for signal in record['signal_data']:
        # Suponiendo que 'samp' contiene las muestras de señal en milisegundos
        signal_data = signal['samp']
        num_samples = len(signal_data)  # Número de muestras en la señal

        # Agregar los valores de señal a 'y'
        y.append(signal_data)

        # Agregar los tiempos (posiciones) a 'X'
        # Aquí 'X' sería una lista de listas donde cada sublista contiene los tiempos
        X.append(list(range(num_samples)))

# Convertir a arrays de NumPy
X = np.array(X)
y = np.array(y)

# Asegurarse de que los datos sean de tipo float32 y estén normalizados si es necesario
X = X.astype('float32')
y = y.astype('float32')
# Realizar normalización si es necesario

# Ajustar las dimensiones de entrada según la estructura de tus datos
num_samples = X.shape[1] if len(X.shape) > 1 else 1  # número de muestras por señal
num_channels = X.shape[2] if len(X.shape) > 2 else 1  # número de canales (leads)

# Definir la arquitectura del modelo
model = Sequential([
    Flatten(input_shape=(num_samples, num_channels)),
    Dense(64, activation='relu'),
    Dense(1, activation='sigmoid')
])

# Compilar el modelo
model.compile(optimizer=Adam(), loss='mean_squared_error', metrics=['accuracy'])

# Entrenar el modelo
model.fit(X, y, epochs=10, validation_split=0.2)

# Guardar el modelo entrenado en formato .h5
model_path = './models/ecg_model.h5'
model.save(model_path)

print("Modelo entrenado y guardado exitosamente.")

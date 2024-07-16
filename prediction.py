import os
import numpy as np
from tensorflow.keras.models import load_model

# Ruta al archivo del modelo
model_path = './models/ecg_model.h5'

# Verificar si el archivo del modelo existe
if not os.path.exists(model_path):
    raise FileNotFoundError(f"El archivo del modelo no se encontró en la ruta: {model_path}")

# Cargar el modelo
model = load_model(model_path)

def predict_arrhythmia(samples):
    # Lista para almacenar las predicciones individuales
    predictions = []

    # Iterar sobre cada subarray de 2500 datos en samples
    for sample in samples:
        # Convertir la lista a un array de NumPy y asegurar la forma correcta
        sample_array = np.array(sample)
        sample_array = sample_array.reshape(1, -1)

        # Realizar predicción usando el modelo para el subarray actual
        prediction = float(model.predict(sample_array))  # Obtener la predicción como float
        predictions.append(prediction)

    return predictions

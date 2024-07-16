import os
from tensorflow.keras.models import load_model

# Ruta al archivo del modelo
model_path = './models/ecg_model.h5'

# Verificar si el archivo del modelo existe
if not os.path.exists(model_path):
    raise FileNotFoundError(f"El archivo del modelo no se encontró en la ruta: {model_path}")

# Cargar el modelo
model = load_model(model_path)

# Mostrar el resumen del modelo
model.summary()

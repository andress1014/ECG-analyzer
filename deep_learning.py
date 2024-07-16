import os
from pymongo import MongoClient
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv1D, Flatten, MaxPooling1D
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

# Conexión a MongoDB
client = MongoClient(mongo_uri)
db = client.ecg_database
collection = db.ecg_signals

def extract_data():
    # Obtener los datos de MongoDB
    data = list(collection.find({}))

    # Preparar los datos
    X = []
    y = []

    for record in data:
        signal_data = record.get('signal_data', [])
        if len(signal_data) == 12:  # Asegúrate de que haya 12 señales
            signals = [signal['samp'] for signal in signal_data]
            X.append(signals)
            y.append(record.get('transaction_id'))  # Puedes cambiar esto por la etiqueta adecuada

    X = np.array(X)
    y = np.array(y)

    # Normalizar los datos
    X = X / np.max(np.abs(X), axis=1, keepdims=True)

    # Convertir las etiquetas a categóricas (si es necesario)
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)
    y = to_categorical(y)

    return X, y

def create_ann_model(input_shape, num_classes):
    model = Sequential()
    model.add(Dense(64, activation='relu', input_shape=input_shape))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def create_cnn_model(input_shape, num_classes):
    model = Sequential()
    model.add(Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Flatten())
    model.add(Dense(64, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def train_and_evaluate_models():
    X, y = extract_data()

    # Dividir los datos en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Crear y entrenar el modelo ANN
    ann_model = create_ann_model((12, X_train.shape[2]), y_train.shape[1])
    ann_model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test))

    # Crear y entrenar el modelo CNN
    cnn_model = create_cnn_model((12, X_train.shape[2]), y_train.shape[1])
    cnn_model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test))

    # Evaluar los modelos
    ann_score = ann_model.evaluate(X_test, y_test)
    cnn_score = cnn_model.evaluate(X_test, y_test)

    return ann_score[1], cnn_score[1]

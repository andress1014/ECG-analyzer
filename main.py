from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from migration import migrate_data
from process_data import process_ecg_data
from register_doc import update_history_commentary
from deep_learning import train_and_evaluate_models
from list_patients import list_patients  # Asegúrate de tener este archivo
from user_details import router as user_details_router
from prediction import predict_arrhythmia  # Importa la función de predicción

# Importar las funciones o clases necesarias para trabajar con MongoDB
from pymongo import MongoClient
import os
from dotenv import load_dotenv

app = FastAPI()

# Configura los orígenes permitidos para CORS (puedes ajustar los dominios según tu entorno)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Esto permite acceso desde cualquier origen, ajusta según necesites
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URI de MongoDB desde las variables de entorno
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

# Conectar a MongoDB
mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client.ecg_database
mongo_collection = mongo_db.ecg_signals

class CommentaryUpdate(BaseModel):
    transaction_id: str
    commentary: str

@app.get("/migrate")
def run_migration():
    migration_result = migrate_data()
    return {"message": migration_result}

@app.get("/process_data")
def process_data(id_migration: str = Query(..., description="Unique identifier for the migration batch")):
    try:
        result = process_ecg_data(id_migration=id_migration)
        if "message" in result and "Error" in result["message"]:
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@app.post("/commentary")
def update_commentary(update: CommentaryUpdate):
    try:
        result = update_history_commentary(update.transaction_id, update.commentary)
        if "message" in result and "Error" in result["message"]:
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating commentary: {str(e)}")

@app.get("/deep_learning_data")
def deep_learning_data():
    try:
        ann_accuracy, cnn_accuracy = train_and_evaluate_models()
        return {"ann_accuracy": ann_accuracy, "cnn_accuracy": cnn_accuracy}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training models: {str(e)}")

@app.get("/list_patients")
def get_patients():
    try:
        patients = list_patients()
        return patients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing patients: {str(e)}")

@app.get("/user_details")
def get_user_details(transaction_id: str = Query(..., description="Transaction ID to fetch user details")):
    try:
        # Consultar MongoDB usando el transaction_id
        result = mongo_collection.find_one({"transaction_id": transaction_id})

        if result:
            # Convertir ObjectId a str para la respuesta JSON si es necesario
            result["_id"] = str(result["_id"])
            return result
        else:
            raise HTTPException(status_code=404, detail="Transaction ID not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user details: {str(e)}")
    
# Definir el endpoint para predecir arritmia
# Definir el endpoint para predecir arritmia
@app.get("/predict_arrhythmia")
def predict_arrhythmia_endpoint(transaction_id: str = Query(..., description="Transaction ID of the ECG record")):
    try:
        # Consultar MongoDB usando el transaction_id
        result = mongo_collection.find_one({"transaction_id": transaction_id})
        if result:
            # Extraer las señales (samplings) del ECG
            signal_data = result['signal_data']
            samples = [lead['samp'] for lead in signal_data]
            
            # Realizar predicción usando la función importada
            prediction = predict_arrhythmia(samples)

            # Devolver el resultado de la predicción en formato JSON
            return {"transaction_id": transaction_id, "prediction": prediction}
        else:
            raise HTTPException(status_code=404, detail="Transaction ID not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting arrhythmia: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the ECG Data Migration API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

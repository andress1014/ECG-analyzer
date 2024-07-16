from fastapi import APIRouter, HTTPException, Query
from pymongo import MongoClient
import os
from dotenv import load_dotenv

router = APIRouter()

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URI de MongoDB desde las variables de entorno
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

# Conectar a MongoDB
mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client.ecg_database
mongo_collection = mongo_db.ecg_signals

@router.get("/user_details")
async def get_user_details(transaction_id: str = Query(..., description="Transaction ID to fetch user details")):
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

# Cerrar el cliente de MongoDB al finalizar
@router.on_event("shutdown")
def shutdown_mongo_client():
    mongo_client.close()

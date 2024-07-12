from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from migration import migrate_data
from process_data import process_ecg_data
from register_doc import update_history_commentary

app = FastAPI()

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

@app.get("/")
def read_root():
    return {"message": "Welcome to the ECG Data Migration API"}

from fastapi import FastAPI, HTTPException, Query
from migration import migrate_data
from process_data import process_ecg_data

app = FastAPI()

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

@app.get("/")
def read_root():
    return {"message": "Welcome to the ECG Data Migration API"}

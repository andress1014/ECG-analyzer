from fastapi import FastAPI, HTTPException
from migration import migrate_data
from process_data import process_ecg_data

app = FastAPI()

@app.get("/migrate")
def run_migration():
    migration_result = migrate_data()
    return {"message": migration_result}

@app.get("/process_data")
def process_data_endpoint():
    result = process_ecg_data()
    if 'error' in result:
        raise HTTPException(status_code=500, detail=result['message'])
    return result


@app.get("/")
def read_root():
    return {"message": "Welcome to the ECG Data Migration API"}

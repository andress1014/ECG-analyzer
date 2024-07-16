import os
import mysql.connector
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno para MySQL
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mysql_user = os.getenv('MYSQL_USER', 'root')
mysql_password = os.getenv('MYSQL_PASSWORD', '')
mysql_database = os.getenv('MYSQL_DATABASE', 'ecg')

# Obtener las variables de entorno para MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

def list_patients():
    # Conectar a MySQL
    mysql_conn = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )
    mysql_cursor = mysql_conn.cursor(dictionary=True)

    # Conectar a MongoDB
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client.ecg_database
    mongo_collection = mongo_db.ecg_signals

    try:
        # Obtener los datos de la tabla history en MySQL
        mysql_cursor.execute("SELECT transaction_id FROM history")
        history_records = mysql_cursor.fetchall()

        patients = []

        for record in history_records:
            transaction_id = record['transaction_id']
            # Obtener la información de user_info desde MongoDB
            mongo_record = mongo_collection.find_one({"transaction_id": transaction_id}, {"_id": 0, "user_info": 1})
            if mongo_record:
                patients.append({
                    "transaction_id": transaction_id,
                    "user_info": mongo_record.get("user_info")
                })

        return patients

    finally:
        # Cerrar las conexiones a la base de datos
        mysql_cursor.close()
        mysql_conn.close()
        mongo_client.close()

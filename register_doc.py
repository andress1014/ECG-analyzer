import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mysql_database = os.getenv('MYSQL_DATABASE', 'ecg')
mysql_user = os.getenv('MYSQL_USER', 'your_username')
mysql_password = os.getenv('MYSQL_PASSWORD', 'your_password')

def update_history_commentary(transaction_id: str, commentary: str):
    try:
        # Conexión a MySQL
        connection = mysql.connector.connect(
            host=mysql_host,
            database=mysql_database,
            user=mysql_user,
            password=mysql_password
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Actualizar el campo commentary en la tabla history
            cursor.execute("""
            UPDATE history
            SET commentary = %s
            WHERE transaction_id = %s
            """, (commentary, transaction_id))

            connection.commit()
            cursor.close()
            connection.close()
            return {"message": "Commentary updated successfully"}
    except Error as e:
        return {"message": f"Error connecting to MySQL: {str(e)}"}
